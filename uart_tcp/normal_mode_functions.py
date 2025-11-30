# Modified functions for normal mode operation

async def start_client_normal_mode(ssid, pwd, ip, port, verbose=True):
    """Connect in normal mode (not transparent) for reliable AT+CIPSEND flow control."""
    try:
        uart.write(b'+++')
    except:
        pass
    
    await asyncio.sleep_ms(1200)
    await _drain_uart_once(80)

    steps = [
        ('AT', ('OK',)),
        ('ATE0', ('OK',)),
        ('AT+CWMODE=3', ('OK',)),
        ('AT+CWJAP="%s","%s"' % (ssid, pwd), ('OK','ALREADY CONNECTED','FAIL')),
        ('AT+CIFSR', ('OK',)),
        ('AT+CIPMUX=0', ('OK',)),  # Single connection mode
        ('AT+CIPSTART="TCP","%s",%s' % (ip, port), ('OK','ALREADY CONNECTED','ERROR')),
    ]
    
    for cmd, expect in steps:
        ok = await send_at(cmd, expect=expect, timeout_ms=20000 if 'CWJAP' in cmd else 8000, verbose=verbose)
        
        if not ok:
            if verbose:
                print('Failed step:', cmd)
            return False
        
        await asyncio.sleep_ms(50)

    # Stay in normal mode - no CIPMODE=1
    TRANSPARENT_MODE[0] = False
    TRANSPARENT_READY[0] = False
    
    if verbose:
        print('Client connected in normal mode (AT+CIPSEND)')
    
    return True


async def sender_normal_mode(msg_q, swriter):
    """Sender using normal mode AT+CIPSEND with proper flow control."""
    global send_sem
    print('sender start (normal mode)...')
    
    while True:
        msg = await msg_q.get()
        
        try:
            if isinstance(msg, tuple):
                msgId, payload = msg
            else:
                payload, msgId = msg, None

            # Encode payload with newline
            if isinstance(payload, str):
                payload_bytes = payload.encode() + b'\n'
            else:
                payload_bytes = payload + b'\n'

            async with send_sem:
                await msg_bucket.consume(1)
                
                # Normal mode: AT+CIPSEND=<length>
                cmd = 'AT+CIPSEND=%d' % len(payload_bytes)
                ok = await send_at(cmd, expect=('>',), timeout_ms=5000, verbose=False)
                
                if not ok:
                    print('AT+CIPSEND failed for msgId:', msgId)
                    continue
                
                # Send the payload after receiving '>'
                await swriter.awrite(payload_bytes)
                LAST_TX_MS[0] = time.ticks_ms()
                
                # Wait for SEND OK
                ok = await wait_token('SEND OK', timeout_ms=5000)
                
                if ok:
                    print('Send OK (normal) msgId:', msgId)
                else:
                    print('SEND OK timeout for msgId:', msgId)
                    
        except Exception as ex:
            print("sender error:", ex)


async def wait_token(token: str, timeout_ms=3000) -> bool:
    """Wait for a specific token from the UART reader without sending a command."""
    evt = asyncio.Event()
    _pending[token] = evt
    
    try:
        await asyncio.wait_for(evt.wait(), timeout_ms/1000)
        return True
    except asyncio.TimeoutError:
        return False
    finally:
        _pending.pop(token, None)
