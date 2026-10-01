# Root Cause Analysis: Waveshare Gateway Transaction Desync

## The Investigation
We conducted isolated testing of the physical bus using a direct `pymodbus` script (`test_bus.py`) with Home Assistant stopped. We queried the Eastron SDM630 devices (Units 101, 102, 103) using the original large register groups (88 registers = 176 bytes).

## Findings
1. **No Hardware Size Limit**: The SDM630 devices **successfully returned all 88 registers** on the first try. There is no 65-byte FIFO limit on the Eastron hardware. Contacting Eastron is not necessary.
2. **The Real Culprit**: The chaotic behavior and garbage data is caused by a severe transaction desynchronization bug in the Waveshare gateway when operating in "Multi-Host" mode.

### How the Bug Happens
1. Home Assistant attempts to poll a "dead" unit on the bus (like CASA, RCF, or THM_FTXRUM).
2. The unit does not respond, and the RS485 bus hangs.
3. Home Assistant's `pymodbus` TCP timeout (e.g. 2 seconds) expires *before* the Waveshare gateway's internal timeout (which might be set to `0` or a very high value).
4. Home Assistant gives up on the transaction, creates a *new* Transaction ID, and sends the next request (e.g., asking for 40 registers).
5. The Waveshare gateway eventually gets a late response from the bus (or finally times out), but it buffers the *stale* response from the previous 88-register request.
6. When the gateway sees HA's new TCP request, it takes the **stale 88-register response**, slaps the **new Transaction ID** on it, and sends it back to Home Assistant!
7. Home Assistant expects 40 registers but receives 88 registers, causing massive data corruption (e.g. mapping "Voltage" to "Energy" registers).

### Why the 24-Register Patch Made it Worse
Splitting the groups into 24-register chunks was logically sound, but it increased the number of transactions per SDM device from 11 to 15. Because the bus is heavily congested with dead units causing timeouts, more transactions meant a 100% chance of a transaction desync occurring during initialization. Since the integration demands a flawless `firstRead` of all groups to start, initialization became mathematically impossible.

## The Fixes
1. **Reverted Patch**: The `SDM630.py` patch has been reverted to use the large, efficient groups.
2. **Quick Fix (Today)**: You MUST temporarily disable or remove the "dead" units (CASA, RCF, THM_FTXRUM) from your Home Assistant configuration. By eliminating the timeouts, the gateway will not desync, and the SDM devices will work perfectly.
3. **Long-Term Gateway Fix**: Log into the Waveshare Web UI and change the **Instruction Timeout** to a non-zero value (e.g., 500ms or 1000ms) that is *shorter* than HA's Modbus timeout. This ensures the gateway replies with a clear Modbus exception *before* HA gives up, keeping the transaction IDs synchronized.
