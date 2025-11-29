# Notes:
#   * Keep only ONE reader of uart: uart_reader_loop().
#   * Writer uses awrite() only; no toggling.
#   * AT replies are matched by tokens (OK, >, ERROR). You can expand this per command.
#
from machine import UART, Pin
import uasyncio as asyncio
import ujson
import gc
from queue import Queue
import ubinascii, uhashlib, os
import json
import re

SSID = 'Cudy24G'         # <-- change if needed
PASSWORD = 'ZAnne19991214'
PORT = '8080'
UART_ID = 0
MQTT_BROKER = '192.168.10.124'
BAUD = 115200
TX_PIN = None  # Use default pins for UART(0) on your board
RX_PIN = None
_in_hash_md5 = None
fout = None

# ----------------- UART + Streams -----------------
uart = UART(UART_ID, BAUD) if (TX_PIN is None or RX_PIN is None) else UART(UART_ID, BAUD, tx=TX_PIN, rx=RX_PIN)
sreader = asyncio.StreamReader(uart)
swriter = asyncio.StreamWriter(uart, {})
error_q = []
success_q = []

# ----------------- Globals -----------------
# AT waiter registry: token -> Future
_pending = {}  # e.g. {'OK': Future, '>': Future, 'ERROR': Future}

# Queues for your app
recv_q = Queue()  # inbound app payloads (e.g. from +IPD)
send_q = Queue()  # outbound app payloads (raw TCP writes)
_at_lock = asyncio.Lock()

#mqtt helpers
# ---- MQTT packet builders (CONNECT / PUBLISH QoS0 / PINGREQ) ----

def _enc_varint(n: int) -> bytes:
    # MQTT Remaining Length varint
    out = bytearray()
    while True:
        byte = n % 128
        n //= 128
        if n > 0:
            byte |= 0x80
        out.append(byte)
        if n == 0:
            break
    return bytes(out)

def _enc_utf8(s: str) -> bytes:
    b = s.encode('utf-8')
    return len(b).to_bytes(2, 'big') + b


# Minimal AT helpers if you don't already have them:

uart = UART(1, 115200)
uart.read()

async def send_at_new(cmd, expect=('OK',), timeout_ms=5000, verbose=False):
    if verbose: print("AT>>", cmd)
    uart.write(cmd + "\r\n")
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    buf = b""
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if uart.any():
            buf += uart.read() or b""
            if verbose and b"\r\n" in buf:
                for line in buf.split(b"\r\n"):
                    if line:
                        print("<", line)
            if any(tok.encode() in buf for tok in expect):
                return True
            if b"ERROR" in buf or b"FAIL" in buf:
                return False
        await asyncio.sleep_ms(5)
    return False

# Switch these to True if you choose transparent mode
TRANSPARENT_MODE  = [False]
TRANSPARENT_READY = [False]

async def tcp_connect(host, port, *, transparent=False):
    # escape any previous data mode
    try: uart.write(b'+++')
    except: pass
    await asyncio.sleep_ms(1200); _ = uart.read()

    ok  = await send_at("AT")
    ok &= await send_at("ATE0")
    ok &= await send_at("AT+CWMODE=1")
    ok &= await send_at('AT+CWJAP="SSID","PASS"', expect=('OK','ALREADY CONNECTED','WIFI CONNECTED'), timeout_ms=20000)
    ok &= await send_at("AT+CIFSR")
    ok &= await send_at("AT+CIPMUX=0")  # single link for simplicity
    ok &= await send_at('AT+CIPSTART="TCP","%s",%d' % (host, port), expect=('OK','ALREADY CONNECTED'), timeout_ms=8000, verbose=True)
    if not ok: return False

    if transparent:
        ok &= await send_at("AT+CIPMODE=1")
        ok &= await send_at("AT+CIPSEND", expect=('>',), timeout_ms=3000)
        TRANSPARENT_MODE[0] = TRANSPARENT_READY[0] = bool(ok)
    else:
        TRANSPARENT_MODE[0] = TRANSPARENT_READY[0] = False
    return ok

async def tcp_send(buf: bytes):
    if TRANSPARENT_MODE[0] and TRANSPARENT_READY[0]:
        uart.write(buf)
        return True
    # normal mode: must request prompt with exact length
    ok = await send_at('AT+CIPSEND=%d' % len(buf), expect=('>',), timeout_ms=3000)
    if not ok: return False
    uart.write(buf)
    return True

# Minimal CONNACK reader — works in both normal and transparent modes.
# In transparent, bytes arrive as-is; in normal mode they are wrapped in +IPD.

def _extract_ipd_frames(accum: bytearray):
    """Return list of payloads from +IPD frames; mutate 'accum'."""
    out = []
    while True:
        p = accum.find(b'+IPD,')
        if p < 0: break
        c = accum.find(b':', p)
        if c < 0: break
        header = accum[p:c]
        parts = header.split(b',')
        try:
            length = int(parts[-1])
        except:
            del accum[:p+5]; continue
        if len(accum) < c+1+length: break
        payload = bytes(accum[c+1:c+1+length])
        del accum[:c+1+length]
        out.append(payload)
    return out

async def wait_connack(timeout_ms=5000):
    deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
    accum = bytearray()
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if uart.any():
            accum += uart.read() or b""
            # If normal mode, peel +IPD frames to get raw MQTT
            if not TRANSPARENT_MODE[0]:
                for pl in _extract_ipd_frames(accum):
                    if pl.startswith(b'\x20\x02'):  # CONNACK, remaining length 2
                        # pl = 0x20 0x02 [ack flags] [return code]
                        return pl[3] == 0  # return code 0 = success
            else:
                # Transparent: look directly for CONNACK
                i = accum.find(b'\x20\x02')
                if i >= 0 and len(accum) >= i+4:
                    return accum[i+3] == 0
        await asyncio.sleep_ms(10)
    return False

async def mqtt_connect_session(client_id, keepalive=30, user="", pwd=""):
    pkt = mqtt_connect_pkt(client_id, keepalive, user, pwd, clean=True)
    ok  = await tcp_send(pkt)
    if not ok: return False
    ok  = await wait_connack()
    return ok

async def mqtt_publish_qos0(topic: str, payload: str | bytes, retain=False):
    pkt = mqtt_publish_qos0_pkt(topic, payload, retain=retain)
    return await tcp_send(pkt)

async def mqtt_ping( ) -> bool:
    return await tcp_send(mqtt_pingreq_pkt())

async def mqtt_connect(broker, port=1883, client_id="pico", user="", pwd="", ssl=False):
    scheme = 2 if ssl else 1
    ok  = await send_at(f'AT+MQTTUSERCFG=0,{scheme},"{client_id}","{user}","{pwd}",0,0,""', expect=('OK',))
    ok &= await send_at(f'AT+MQTTCONN=0,"{broker}",{port},{1 if ssl else 0}', expect=('OK','ALREADY CONNECTED'))
    return bool(ok)

async def mqtt_pub(topic, payload, qos=0, retain=0):
    # payload must be a simple string; escape quotes if needed
    return await send_at(f'AT+MQTTPUB=0,"{topic}","{payload}",{qos},{retain}', expect=('OK',))

async def mqtt_sub(topic, qos=0):
    return await send_at(f'AT+MQTTSUB=0,"{topic}",{qos}', expect=('OK',))

def _maybe_set(token: str):
    evt = _pending.get(token)
    
    if evt:
        try:
            evt.set()
        except Exception:
            pass

async def send_at(cmd: str, expect=('OK',), timeout_ms=5000) -> bool:
    """Write an AT command and await one of expected tokens from the reader loop (MicroPython-friendly).
       Uses asyncio.Event in place of Future/create_future.
    """
    async with _at_lock:
        evt = asyncio.Event()
        
        for t in expect:
            _pending[t] = evt
            
        try:
            await swriter.awrite(cmd + '\r\n')
            await asyncio.wait_for(evt.wait(), timeout_ms/1000)
            
            return True
        except asyncio.TimeoutError:
            return False
        finally:
            for t in expect:
                _pending.pop(t, None)

async def start_tcp_server_static_sta(ssid, pwd,
                                      ip="192.168.1.50",
                                      gw="192.168.1.1",
                                      mask="255.255.255.0",
                                      port=8080):
    # Basic sanity + disable echo
    ok = await send_at('AT', expect=('OK',), timeout_ms=1500)
    ok = ok and await send_at('ATE0', expect=('OK',), timeout_ms=1000)
    
    if not ok:
        print("AT sanity failed");
        return False

    # Station mode & join Wi-Fi
    ok = await send_at('AT+CWMODE=1', expect=('OK',), timeout_ms=1500)
    ok = ok and await send_at('AT+CWJAP="%s","%s"' % (ssid, pwd),
                              expect=('OK','ALREADY CONNECTED','FAIL'),
                              timeout_ms=20000)
    
    if not ok:
        print("CWJAP failed"); return False

    ok = ok and await send_at('AT+CIPSTA="%s","%s","%s"' % (ip, gw, mask),
                              expect=('OK',), timeout_ms=2000)
    
    if not ok:
        print("CIPSTA failed"); return False

    # Confirm IP
    ok = ok and await send_at('AT+CIFSR', expect=(ip, 'OK'), timeout_ms=2000)
    
    if not ok:
        print("CIFSR didn’t show the static IP"); return False

    # Server setup
    ok = ok and await send_at('AT+CIPMUX=1', expect=('OK',), timeout_ms=1000)
    
    if not ok:
        print("CIPMUX failed"); return False

    ok = ok and await send_at('AT+CIPSERVER=1,%d' % port, expect=('OK',), timeout_ms=1500)
    
    if not ok:
        print("CIPSERVER start failed"); return False

    # Note: AT+CIPSERVER? query not supported by all ESP8266 firmware versions
    # Server is already confirmed started by the OK response above
    
    print("TCP server listening on %s:%d" % (ip, port))

    ok &= await send_at('AT+CIPSTART=%d,"TCP","%s",%d' % (4, "192.168.10.174", 1883),
                        expect=('OK','ALREADY CONNECTED'), timeout_ms=8000)
    if not ok:
        print("Bring-up failed")
    else:
        print("TCP server on %d, MQTT link id %d to %s:%d" % (1883, 4, "192.168.10.174", 1883))

    return True

async def start_esp_server(ssid: str, pwd: str, port: str = '8080') -> bool:
    """Bring up ESP8266 and start a multi-connection TCP server on the given port."""
    steps = [
        ('AT', ('OK',)),
        ('AT+CWMODE=3', ('OK',)),
        ('AT+CWJAP="%s","%s"' % (ssid, pwd), ('OK', 'ALREADY CONNECTED', 'FAIL')),
        ('AT+CIPMUX=1', ('OK',)),
        ('AT+CIPSERVER=1,%s' % port, ('OK', 'ERROR')),
        ('AT+CIFSR', ('OK',)),
    ]
    
    for cmd, expect in steps:
        ok = await send_at(cmd, expect=expect, timeout_ms=20000 if 'CWJAP' in cmd else 5000)
        
        if not ok:
            print('Failed step:', cmd)
            return False
        
        await asyncio.sleep_ms(50)  # small pacing
        
    print('ESP8266 TCP server started on port', port)
    return True

def clean_and_load_json(raw):
    # 1. Strip leading/trailing whitespace
    s = raw.strip()

    # 2. Remove common prefixes like +IPD,0,174:
    #    Looks for the first "{" and trims everything before it
    if not s.startswith("{") and "{" in s:
        s = s[s.index("{"):]

    # 3. Remove trailing junk after the last "}"
    if not s.endswith("}") and "}" in s:
        s = s[:s.rindex("}")+1]

    # 4. Debug: show exactly what string will be parsed
    print("Parsing JSON string:", repr(s))

    # 5. Try to parse
    return json.loads(s)

async def handle_json(obj):
    print("JSON received:", obj)
    
async def readline(sreader, limit=1024):
    """Minimal readline() for MicroPython StreamReader.
       Returns bytes up to and including b'\\n' or until limit reached."""
    buf = bytearray()
    
    while True:
        ch = await sreader.read(1)
        
        if not ch:
            # EOF or no data
            return bytes(buf)
        
        buf += ch
        
        if ch == b'\n' or len(buf) >= limit:
            return bytes(buf)

# inside your UART read loop
def extract_ipd_frames(buf: bytearray):
    frames = []
    while True:
        p = buf.find(b'+IPD,')
        if p < 0: break
        c = buf.find(b':', p)
        if c < 0: break
        header = buf[p:c]                 # e.g. b'+IPD,0,96'
        parts = header.split(b',')
        if len(parts) < 3:                # malformed
            del buf[:p+5]; continue
        link_id = int(parts[1])
        length  = int(parts[2])
        if len(buf) < c+1+length:         # wait for full payload
            break
        payload = bytes(buf[c+1:c+1+length])
        del buf[:c+1+length]
        frames.append((link_id, payload))
    return frames

# when you get a frame:
#for link_id, payload in extract_ipd_frames(rx_buf):
    # Here payload may be newline-terminated JSON your client sent
    #reply = payload  # pure echo; or build your own JSON/ACK
    #cmd = f'AT+CIPSEND={link_id},{len(reply)}'
    #ok = await send_at(cmd, expect=('>',), timeout_ms=4000)
    #if ok:
        #await swriter.awrite(reply)  # no extra '\n' unless you want it

async def json_line_reader_stream(
    recv_q,
    sreader,
    *,
    on_text=None,                 # async callback(str): for non-JSON lines
    encoding='utf-8',
    max_line_bytes=8192,
    ignore_non_json=False,        # if True and no on_text, non-JSON lines are dropped
    json_predicate=None           # optional: callable(str)->bool to decide if we try JSON
):
    """
    Read newline-terminated frames from a StreamReader and handle JSON or plain text.

    - sreader: asyncio StreamReader
    - on_json: async callback taking a Python object (json-decoded)
    - on_text: async callback taking a 'str' for non-JSON lines (optional)
    - encoding: input bytes→str codec
    - max_line_bytes: guardrail against runaway lines
    - ignore_non_json: if True and on_text is None, silently drop non-JSON lines
    - json_predicate: custom detector; default = str.lstrip startswith('{') or '['
    """
    if json_predicate is None:
        def json_predicate(s: str) -> bool:
            s = s.lstrip()
            return s.startswith('{') or s.startswith('[')

    while True:
        line = await readline(sreader)

        if not line:
            # EOF or no data; yield briefly to avoid a tight loop
            await asyncio.sleep_ms(1)
            continue

        # Guardrail
        if len(line) > max_line_bytes:
            # Try not to blow RAM — drop this line
            # You could optionally call on_text with a truncated preview here
            # if you want to observe oversized lines.
            continue

        # Trim LF then optional CR
        if line.endswith(b'\n'):
            line = line[:-1]
            
        if line.endswith(b'\r'):
            line = line[:-1]
            
        if not line:
            continue

        try:
            text = line.decode(encoding)
            print("json_line_reader_stream:  " + str(text))            
        except Exception as ex:
            # Fallback: best-effort replacement chars
            text = line.decode(encoding, 'ignore')

        idx = text.find("+IPD")

        # process data packet
        if idx != -1:
#            print("Raw data length: " + str(len(text)))            
 #           print("Raw data...")
  #          print(text)

            chunks = text.split("+IPD")

            for chunk in chunks:
                chunk = chunk.strip()
                
                if not chunk:
                    continue

                # find start of JSON
                idx = chunk.find("{")
                
                if idx == -1:
                    continue

                json_str = chunk[idx:]

                # Decide JSON vs text
                if json_predicate(json_str):
                    try:
                        msg = json.loads(json_str)
                        await recv_q.put(msg)                                                    
                        continue
                    except Exception:
                        # Fall through to on_text if parse fails
                        pass

        # Non-JSON or JSON parse failed
        else:
            print('[UART]', line)

            if b'OK' in line:
                _maybe_set('OK')
                
            if b'>' in line:
                _maybe_set('>')
                
            if b'ERROR' in line:
                _maybe_set('ERROR')
                
            if b'FAIL' in line:
                _maybe_set('FAIL')
                
            if b'ALREADY CONNECTED' in line:
                _maybe_set('ALREADY CONNECTED')

# -------------- Example "sender" (raw TCP writes) --------------
# You will still need to wrap messages with CIPSend/CIPSENDEX for a specific connection id.
# The higher-level app should place properly formatted CIP commands into send_q.
async def sender_loop(send_q):
    while True:
        data = await send_q.get()
        
        try:
            print('Data to send:')
            print(str(data))
            link_id = 0

            cmd = f'AT+CIPSEND={link_id},{len(data)}'
            ok = await send_at(cmd, expect=('OK',), timeout_ms=4000)
            
            if ok:
                await swriter.awrite(data)  # no extra '\n' unless you want it

            print('Msg sent OK...\r')
        except Exception as ex:
            print('sender_loop error:', ex)

# -------------- Simple dispatcher for +IPD lines --------------
async def recv_queue_processor(recv_q, send_q):
    while True:
        msg = await recv_q.get()
        
        category = msg["Category"]        

        if category == 'Files':
            await handle_files(msg)
        elif category == 'Test':
            await handle_test(msg, send_q)
        else:
            print('RX:', obj)

# -------- Concrete Handlers (ported) --------
# Files: 3-step protocol: Header -> Content -> End
#   Header: {'Category':'Files','Step':'Header','FileName': 'name.ext'}
#   Content: {'Category':'Files','Step':'Content','FileName': 'name.ext','FileData': base64,'ProgressPercentage': n,'FileBlockSequenceNumber': n}
#   End: {'Category':'Files','Step':'End','FileName': 'name.ext','HashData': base64_of_sha256}
async def handle_files(msg, send_queue):
    global _in_hash_md5, fout
    step = msg.get('Step')
    try:
        if step == 'Header':
            _in_hash_md5 = uhashlib.sha256()
            file_name = msg['FileName']
            # mirror original path behavior
            os.makedirs('backups', exist_ok=True)
            path = 'backups/copy-' + file_name
            fout = open(path, 'wb')
        elif step == 'Content':
            data_b64 = msg.get('FileData', '')
            chunk = ubinascii.a2b_base64(data_b64) if isinstance(data_b64, str) else data_b64
            if _in_hash_md5 is not None:
                _in_hash_md5.update(chunk)
            if fout:
                fout.write(chunk)
            pp = msg.get('ProgressPercentage')
            seq = msg.get('FileBlockSequenceNumber')
            if pp is not None: print('Progress Percentage:', pp)
            if seq is not None: print('Seq Nr:', seq)
        elif step == 'End':
            if fout:
                try: fout.flush()
                except: pass
                try: fout.close()
                except: pass
            got = (_in_hash_md5.digest() if _in_hash_md5 is not None else b'')
            base64_hash = ubinascii.b2a_base64(got)[:-1].decode('utf-8')
            in_msg_hash = msg.get('HashData', '')
            file_name = msg.get('FileName', '')
            if base64_hash == in_msg_hash:
                success_q.append('File copy OK - ' + file_name)
            else:
                error_q.append('File copy failed - ' + file_name)
                error_q.append('source hash: ' + in_msg_hash)
                error_q.append('dest hash: ' + base64_hash)
        else:
            error_q.append('Files: unknown step')
    finally:
        try:
            await send_queue.put(ujson.dumps(msg))
        except Exception as ex:
            error_q.append('Files send_queue error: %s' % ex)

# Test: verify hash of Base64Message and respond with echoed payload + its hash
async def handle_test(msg, send_queue):
    print('Test Category...')
    
    try:
        _md = uhashlib.sha256()
        msg_id = msg.get('Id')
        b64_in = msg.get('Base64Message', '')
        b64_hash_in = msg.get('Base64MessageHash', '')
        clear = ubinascii.a2b_base64(b64_in) if isinstance(b64_in, str) else b64_in
        clear_hash_in = ubinascii.a2b_base64(b64_hash_in) if isinstance(b64_hash_in, str) else b64_hash_in

        _md.update(clear)
        calc = _md.digest()

        if calc != clear_hash_in:
            err = 'test msg hash diff'
            print(err)
            print('b64_in: ' + str(b64_in))
            print('b64_hash_in: ' + str(b64_hash_in))                        
            error_q.append(err)
        else:
            print("Matched OK: " + str(clear))

        _md2 = uhashlib.sha256()
        _md2.update(clear)
        rsp_hash = _md2.digest()
        b64_rsp = ubinascii.b2a_base64(clear)[:-1].decode('utf-8')
        b64_rsp_hash = ubinascii.b2a_base64(rsp_hash)[:-1].decode('utf-8')

        rsp = {
            'Id': msg_id,
            'Category': 'Test',
            'Base64Message': b64_rsp,
            'Base64MessageHash': b64_rsp_hash,
            'RspReceivedOK': True,
        }
        
        await send_queue.put(ujson.dumps(rsp))
    except Exception as ex:
        error_q.append('Test handler error: %s' % ex)

async def heartbeat():
    led = Pin(25, Pin.OUT)
    
    while True:
        await asyncio.sleep_ms(500)
        led(not led())

# -------------- Orchestration --------------
async def main():
       
    # Kick off the single reader and the dispatcher
    reader_task = asyncio.create_task(json_line_reader_stream(recv_q, sreader))    
    sender_task = asyncio.create_task(sender_loop(send_q))
    queue_processor_task = asyncio.create_task(recv_queue_processor(recv_q, send_q))
    asyncio.create_task(heartbeat())    

    useStaticIP = True
    
    if (useStaticIP == False):
        ok = await start_esp_server(SSID, PASSWORD, PORT)
    else:
        #mqtt
        server = "192.168.10.250"
        port = 1883
        
        ok = await start_tcp_server_static_sta(
            ssid="Cudy24G",
            pwd="ZAnne19991214",
            ip="192.168.10.250",
            gw="192.168.10.1",
            mask="255.255.255.0",
            port=8080)
    
    if not ok:
        print('ESP setup failed; stopping.')
        reader_task.cancel()
        sender_task.cancel()
        return

#    mqttOK = await mqtt_connect(MQTT_BROKER)
    
    #if (mqttOK == True):
        #print("MQTT OK...")
    #else:
     #   print("MQTT Failed...")        

    # Example: periodically print free mem
    async def monitor():
        while True:
            gc.collect()
            free = gc.mem_free()
            alloc = gc.mem_alloc()
            total = free + alloc
            pct = free * 100 / total if total else 0
            print('Free mem: %d (%.1f%%)' % (free, pct))
            await asyncio.sleep(3)

#    mon_task = asyncio.create_task(monitor())
    await asyncio.gather(reader_task, sender_task, queue_processor_task)
#    await asyncio.gather(reader_task, mon_task, queue_processor_task)    

# -------------- Entry --------------
def run():
    try:
        asyncio.run(main())
    finally:
        # needed by MicroPython to allow subsequent asyncio.run()
        asyncio.new_event_loop()

if __name__ == '__main__':
    run()
