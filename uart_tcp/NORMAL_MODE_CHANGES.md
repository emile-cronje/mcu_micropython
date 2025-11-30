# Normal Mode Implementation Summary

## Changes Made to uart_tcp_client.py

### 1. Modified start_client() function (lines ~540-570)
**Before**: Set up transparent mode with AT+CIPMODE=1
**After**: Stay in normal mode (CIPMODE=0)

Changes:
- Removed `('AT+CIPMODE=1', ('OK',))` from steps list
- Added `('AT+CIPMUX=0', ('OK',))` to ensure single connection mode
- Removed AT+CIPMODE? verification
- Removed AT+CIPSEND call (transparent mode entry)
- Set `TRANSPARENT_MODE[0] = False` and `TRANSPARENT_READY[0] = False` explicitly
- Updated docstring to "use normal mode for reliable AT+CIPSEND flow control"

### 2. Rewrote sender() function (lines ~580-615)
**Before**: Direct UART writes in transparent mode (swriter.awrite)
**After**: AT+CIPSEND with proper flow control

Flow:
1. Send `AT+CIPSEND=<length>` command
2. Wait for `>` prompt (indicates ready to receive data)
3. Write payload via swriter.awrite()
4. Wait for `SEND OK` confirmation
5. Print status with msgId for tracking

### 3. Added wait_token() helper (lines ~452-467)
**Purpose**: Wait for UART tokens without sending AT commands
**Usage**: Enables waiting for 'SEND OK' after data transmission

Implementation:
- Creates asyncio.Event and registers in _pending dict
- Waits with timeout (default 3000ms)
- Cleans up _pending entry in finally block
- Returns True on success, False on timeout

## Testing Recommendations

1. **Initial test**: Set iTestMsgCount=2, BATCH_SIZE=2
   - Should see: "Send OK (normal) msgId: 1" and "Send OK (normal) msgId: 2"
   - Server should receive both messages
   - Should see "Batch 1 complete" without timeout

2. **Full test**: Set iTestMsgCount=100, BATCH_SIZE=10
   - Should process 10 batches sequentially
   - Each message should get AT+CIPSEND → '>' → data → 'SEND OK' sequence
   - Rate limiting still applies (10 msg/sec via msg_bucket)

## Expected Behavior

**Client logs:**
```
sender start (normal mode)...
Send OK (normal) msgId: 1
Send OK (normal) msgId: 2
...
Batch 1 complete (10/10 messages)
```

**Server logs:**
```
Received: {"Id":1, "RspReceivedOK":true, ...}
Received: {"Id":2, "RspReceivedOK":true, ...}
...
```

## Advantages of Normal Mode

1. **Flow control**: Each message acknowledged before next send
2. **Reliability**: No buffer overflow in ESP-AT firmware
3. **Visibility**: Clear success/failure for each transmission
4. **Synchronization**: Natural pacing via '>' and 'SEND OK' tokens

## Backward Compatibility

- Transparent mode code left intact but unreachable (TRANSPARENT_MODE always False)
- Can be restored by changing start_client() steps list
- No breaking changes to message format or validation logic
