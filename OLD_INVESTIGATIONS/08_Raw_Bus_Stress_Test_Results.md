# RS485 Modbus Raw Bus Stress Test Results

**Date Range:** 2026-09-30 22:59 to 2026-10-01 08:50  
**Target Gateway:** `192.168.1.5:502` (Waveshare Modbus TCP-to-RTU)  
**Environment:** Isolated diagnostic runs (Home Assistant Docker container STOPPED)

### Physical Topology History & Event Log

```
+=======================================================================================================================+
| Date / Time         | Topology & Physical Status                                                                       |
+=======================================================================================================================+
| 2026-09-30 22:50 to | Shortened Test Segment (Diagnostics):                                                           |
| 2026-10-01 18:59    | WAVESHARE (GW) -> THMB50 (50) -> SDM-BVP (103) -> SDM-GH (102) -> SDM-HB (101) -> MAGNA3 (14)  |
|                     | - Cable cut right after MAGNA3 (Unterminated, open stub).                                        |
|                     | - CASA device physically DISCONNECTED (99% confirmed burnt RS485 transceiver).                  |
|                     | - RCF devices (40, 41) physically DISCONNECTED.                                                  |
|                     | - All tests in sections 1 through 13 were executed under this exact topology.                   |
|                     | - Waveshare Conflict Time Gap lowered from 50ms to 20ms on 2026-10-01 morning.                   |
+---------------------+-------------------------------------------------------------------------------------------------+
| 2026-10-01 19:00    | Full Bus Restored & Terminated:                                                                 |
| (Current Baseline)  | Full RS485 bus cable reconnected past MAGNA3 with 120Ω bus termination resistor in place.       |
|                     | - CASA remains DISCONNECTED (confirmed burnt RS485 transceiver).                                 |
|                     | - RCF devices (40, 41) reconnected to bus, but appear electrically dead/unresponsive.           |
|                     | - Downstream devices (Trox, Renke, Swegon, etc.) reconnected.                                   |
+=======================================================================================================================+
```
*Note: QDY30A is completely isolated on a separate physical Waveshare gateway (`192.168.1.6`).*

---

## 1. Connection Architecture: Persistent Socket vs. Reconnect-Per-Request

*Test Timestamp: 2026-09-30 22:59*

| Mode | Device | Iterations | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Persistent Socket | THMB50 (ID 50) | 15 | 100.0% | 6.2 | 2.7 | 29.6 | None |
| Persistent Socket | SDM630-GH (ID 102) | 15 | 80.0% | 6.7 | 3.1 | 15.6 | Timeout:3 |
| Persistent Socket | MAGNA3-HP1 (ID 14) | 15 | 80.0% | 59.3 | 4.0 | 162.7 | Timeout:3 |
| Reconnect Per Request | THMB50 (ID 50) | 15 | 100.0% | 61.5 | 7.3 | 158.9 | None |
| Reconnect Per Request | SDM630-GH (ID 102) | 15 | 100.0% | 34.0 | 7.2 | 340.1 | None |
| Reconnect Per Request | MAGNA3-HP1 (ID 14) | 15 | 100.0% | 9.2 | 6.4 | 22.0 | None |

---

## 2. Single-Device Baseline: Turnaround Delay Limits

Testing each device individually with consecutive requests to find minimum required inter-frame silence.

### Device: THMB50 (Slave ID 50, 2 registers)
| Turnaround Delay | Success | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
|   0.0 ms | 20/20 | 100.0% | 3.6 | 2.4 | 7.9 | None |
|  10.0 ms | 20/20 | 100.0% | 6.3 | 2.8 | 18.8 | None |
|  25.0 ms | 20/20 | 100.0% | 5.0 | 2.7 | 18.2 | None |
|  50.0 ms | 20/20 | 100.0% | 6.8 | 2.6 | 58.7 | None |
| 100.0 ms | 20/20 | 100.0% | 30.7 | 2.9 | 166.3 | None |
| 200.0 ms | 20/20 | 100.0% | 41.4 | 3.8 | 84.5 | None |

### Device: SDM630-BVP (Slave ID 103, 88 registers)
| Turnaround Delay | Success | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
|   0.0 ms | 17/20 |  85.0% | 13.2 | 2.8 | 164.8 | Timeout:3 |
|  10.0 ms | 20/20 | 100.0% | 17.0 | 2.8 | 149.5 | None |
|  25.0 ms | 20/20 | 100.0% | 38.8 | 3.1 | 155.7 | None |
|  50.0 ms | 20/20 | 100.0% | 69.1 | 3.1 | 221.0 | None |
| 100.0 ms | 20/20 | 100.0% | 6.0 | 3.1 | 15.7 | None |
| 200.0 ms | 20/20 | 100.0% | 5.1 | 3.3 | 11.8 | None |

### Device: SDM630-GH (Slave ID 102, 88 registers)
| Turnaround Delay | Success | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
|   0.0 ms | 20/20 | 100.0% | 30.6 | 3.5 | 514.2 | None |
|  10.0 ms | 20/20 | 100.0% | 29.2 | 3.1 | 166.2 | None |
|  25.0 ms | 20/20 | 100.0% | 44.1 | 2.9 | 195.9 | None |
|  50.0 ms | 19/20 |  95.0% | 52.6 | 3.4 | 166.0 | Timeout:1 |
| 100.0 ms | 20/20 | 100.0% | 13.7 | 3.2 | 110.9 | None |
| 200.0 ms | 20/20 | 100.0% | 43.8 | 3.5 | 180.2 | None |

### Device: SDM630-HB (Slave ID 101, 88 registers)
| Turnaround Delay | Success | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
|   0.0 ms | 20/20 | 100.0% | 30.2 | 2.8 | 527.5 | None |
|  10.0 ms | 20/20 | 100.0% | 30.0 | 3.2 | 159.9 | None |
|  25.0 ms | 20/20 | 100.0% | 12.5 | 3.1 | 152.0 | None |
|  50.0 ms | 20/20 | 100.0% | 6.1 | 3.2 | 13.6 | None |
| 100.0 ms | 20/20 | 100.0% | 6.4 | 3.2 | 19.3 | None |
| 200.0 ms | 20/20 | 100.0% | 28.2 | 3.2 | 70.7 | None |

### Device: MAGNA3-HP1 (Slave ID 14, 62 registers)
| Turnaround Delay | Success | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
|   0.0 ms | 20/20 | 100.0% | 41.9 | 2.6 | 605.9 | None |
|  10.0 ms | 20/20 | 100.0% | 25.6 | 2.7 | 171.1 | None |
|  25.0 ms | 20/20 | 100.0% | 27.2 | 3.0 | 105.6 | None |
|  50.0 ms | 20/20 | 100.0% | 16.4 | 2.9 | 160.0 | None |
| 100.0 ms | 18/20 |  90.0% | 68.0 | 3.1 | 173.2 | Timeout:2 |
| 200.0 ms | 20/20 | 100.0% | 35.3 | 3.8 | 158.7 | None |

---

## 3. Payload Size Sensitivity: Small (2 Regs) vs. Large (Full Group)

| Device | Payload Size | Registers | Success Rate | Avg RTT (ms) | Errors |
| :--- | :--- | :---: | :---: | :---: | :--- |
| THMB50 (ID 50) | Small | 2 | 100.0% | 17.7 | None |
| THMB50 (ID 50) | Large | 2 | 100.0% | 4.0 | None |
| SDM630-BVP (ID 103) | Small | 2 | 100.0% | 10.5 | None |
| SDM630-BVP (ID 103) | Large | 88 |  85.0% | 5.9 | Timeout:3 |
| SDM630-GH (ID 102) | Small | 2 | 100.0% | 15.9 | None |
| SDM630-GH (ID 102) | Large | 88 |  85.0% | 30.0 | Timeout:3 |
| SDM630-HB (ID 101) | Small | 2 | 100.0% | 15.6 | None |
| SDM630-HB (ID 101) | Large | 88 |  85.0% | 25.2 | Timeout:3 |
| MAGNA3-HP1 (ID 14) | Small | 2 | 100.0% | 127.1 | None |
| MAGNA3-HP1 (ID 14) | Large | 62 | 100.0% | 178.9 | None |

---

## 4. Multi-Device Interleaved Polling (Cycling All 5 Devices)

Simulating real coordinator polling: `THMB50 -> SDM-BVP -> SDM-GH -> SDM-HB -> MAGNA3 -> ...`

| Turnaround Delay | Overall Success | THMB50 (50) | SDM-BVP (103) | SDM-GH (102) | SDM-HB (101) | MAGNA3 (14) | Dominant Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
|   0.0 ms | 25/60 ( 41.7%) | 12/12 | 0/12 | 0/12 | 9/12 | 4/12 | Timeout |
|  20.0 ms | 26/60 ( 43.3%) | 12/12 | 0/12 | 0/12 | 10/12 | 4/12 | Timeout |
|  50.0 ms | 24/60 ( 40.0%) | 12/12 | 0/12 | 0/12 | 10/12 | 2/12 | Timeout |
|  75.0 ms | 27/60 ( 45.0%) | 12/12 | 0/12 | 0/12 | 10/12 | 5/12 | Timeout |
| 100.0 ms | 26/60 ( 43.3%) | 12/12 | 0/12 | 1/12 | 8/12 | 5/12 | Timeout |
| 150.0 ms | 27/60 ( 45.0%) | 12/12 | 0/12 | 0/12 | 9/12 | 6/12 | Timeout |
| 200.0 ms | 27/60 ( 45.0%) | 12/12 | 0/12 | 0/12 | 9/12 | 6/12 | Timeout |
| 300.0 ms | 28/60 ( 46.7%) | 12/12 | 0/12 | 0/12 | 9/12 | 7/12 | Timeout |

---

## 5. Gateway Behavior: Same-Device vs Different-Device Rapid Switching

Testing whether the bottleneck is pure inter-frame silence OR specifically changing Slave IDs.

| Test Condition | Delay | Success Rate | Details |
| :--- | :---: | :---: | :--- |
| 30x SDM-GH Only (Same Slave ID) | 20 ms | 100.0% | 30/30 successful |
| Alternating GH <-> HB (Switching IDs) | 20 ms | 50.0% | 15/30 successful |
| Alternating GH <-> HB (Switching IDs) | 100 ms | 50.0% | 15/30 successful |
| Alternating GH <-> HB (Switching IDs) | 200 ms | 50.0% | 15/30 successful |

---

## 6. Payload Threshold Discovery (Small vs Medium vs Large)

Targeted isolation test specifically across the three Eastron SDM630 meters (`SDM-BVP 103 -> SDM-GH 102 -> SDM-HB 101`):

| Test Condition | Payload Size | Total Bytes on Wire | Interleaved Success Rate | Result |
| :--- | :---: | :---: | :---: | :--- |
| **Small Payload** | 2 registers | 9 bytes | **30/30 (100.0%)** | `{103: 10/10, 102: 10/10, 101: 10/10}` - Flawless |
| **Medium Payload** | 20 registers | 45 bytes | **30/30 (100.0%)** | `{103: 10/10, 102: 10/10, 101: 10/10}` - Flawless |
| **Large Payload (HA Default)** | 88 registers | 181 bytes | **8/30 ( 26.7%)** | `{103: 3/10, 102: 3/10, 101: 2/10}` - 73% Failure |

---

## 7. Comprehensive Bus Quality Benchmark Per Device

Each device was tested with 50 consecutive queries under its native payload size, with 50ms inter-query silence.

| Device | Slave ID | Registers | Tests | Success Rate | Min RTT | Avg RTT | Median | P95 RTT | Max RTT | Jitter (StdDev) | Signal Health Rating |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| THMB50 | 50 | 2 | 50 | 100.0% |   2.7ms |  36.1ms |   4.1ms | 202.1ms | 264.2ms | ±69.2ms | 🟡 Good (Minor noise/jitter) |
| SDM630-BVP | 103 | 88 | 50 |  94.0% |   3.0ms |  30.6ms |   7.7ms | 163.6ms | 230.2ms | ±58.1ms | 🟡 Good (Minor noise/jitter) |
| SDM630-GH | 102 | 88 | 50 |  94.0% |   3.0ms |  49.7ms |  15.5ms | 191.6ms | 213.5ms | ±61.3ms | 🟡 Good (Minor noise/jitter) |
| SDM630-HB | 101 | 88 | 50 |  94.0% |   3.4ms |  42.0ms |  13.6ms | 174.3ms | 191.2ms | ±54.3ms | 🟡 Good (Minor noise/jitter) |
| MAGNA3-HP1 | 14 | 62 | 50 | 100.0% |   3.1ms |  24.6ms |  11.1ms |  83.3ms | 446.4ms | ±63.4ms | 🟡 Good (Minor noise/jitter) |

---

## 8. Deep Dive: MAGNA3 Signal & Responsiveness Profile

Testing MAGNA3 with varying register count (2, 10, 30, 62) and turnaround delays to isolate its failure profile.

| Register Count | Total Bytes | Delay | Success Rate | Avg RTT | P95 RTT | Max RTT | Errors | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 2 | 9 B |   20ms | 100.0% |  20.3ms | 172.5ms | 187.7ms | None | Normal |
| 2 | 9 B |  100ms | 100.0% | 111.1ms | 221.5ms | 245.0ms | None | Normal |
| 10 | 25 B |   20ms | 100.0% |  95.1ms | 1464.0ms | 2064.7ms | None | High latency |
| 10 | 25 B |  100ms | 100.0% |  21.6ms |  83.2ms |  88.2ms | None | Normal |
| 30 | 65 B |   20ms |  96.0% |  42.8ms | 175.9ms | 178.5ms | Timeout:1 | Instability observed |
| 30 | 65 B |  100ms | 100.0% |  56.3ms | 205.9ms | 218.9ms | None | Normal |
| 62 | 129 B |   20ms | 100.0% | 103.5ms | 1633.8ms | 2318.7ms | None | Latency spikes > 2s |
| 62 | 129 B |  100ms | 100.0% |  64.1ms | 252.7ms | 267.9ms | None | Normal |

---

## 9. Investigation of 94% Rate & Physical Bus Noise Floor

*Test Timestamp: 2026-09-30 23:45:05*

### A. Exact Failure Pattern Analysis on SDM630 Meters
Testing 100 consecutive 88-register queries per meter with 50ms delay to track EXACT failure indices and timing.

| Meter | Total Queries | Successes | Fails | Success Rate | Failed Iteration Indices | Elapsed Times of Failures (s) |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| SDM630-BVP | 100 | 100 | 0 | 100.0% | `None` | `None` |
| SDM630-GH | 100 | 97 | 3 |  97.0% | `0, 1, 2` | `2.5s, 5.1s, 7.6s` |
| SDM630-HB | 100 | 97 | 3 |  97.0% | `0, 1, 2` | `2.5s, 5.1s, 7.6s` |

*(Note: In SDM-GH and SDM-HB, the 3 failures occurred exclusively on iterations 0, 1, and 2 immediately after socket opening during bus wake-up. Iterations 3 through 99 achieved 100.0% zero-error success).*

### B. MAGNA3 Turnaround Silence vs. Waveshare 50ms Conflict Time Gap
Testing MAGNA3 (62 registers) at varying turnaround delays relative to the 50ms Waveshare gap.

| Turnaround Delay | Relation to 50ms Conflict Gap | Queries | Success Rate | Min RTT | Avg RTT | P95 RTT | Max RTT | Spikes > 1.5s |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
|   10 ms | < Gap (Violation) | 40 |  92.5% |   2.8ms |  15.7ms | 165.3ms | 222.8ms | **0/40** |
|   20 ms | < Gap (Violation) | 40 | 100.0% |   2.9ms |   4.7ms |   8.9ms |   9.2ms | **0/40** |
|   40 ms | < Gap (Violation) | 40 |  97.5% |   2.9ms |   5.1ms |  14.0ms |  14.5ms | **0/40** |
|   60 ms | >= Gap (Compliant) | 40 | 100.0% |   2.9ms |  47.8ms | 145.0ms | 148.7ms | **0/40** |
|  100 ms | >= Gap (Compliant) | 40 | 100.0% |   3.1ms |  42.7ms | 167.6ms | 187.8ms | **0/40** |
|  150 ms | >= Gap (Compliant) | 40 |  97.5% |   3.0ms |  37.5ms | 116.6ms | 179.1ms | **0/40** |

### C. Pure Physical Bus Error Rate (Unterminated Bus Noise Floor)
Testing each device with 150 queries with compliant 100ms spacing to isolate pure physical reflection / CRC loss from timing flaws.

| Device | Position on Cable | Registers | Queries | Successes | Physical Frame Drops | Pure Physical Loss Rate | Avg RTT | Assessment |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| THMB50 | Near Gateway (~1m) | 2 | 150 | 150 | 0 | **0.00%** | 39.7ms | 🟢 0% Physical Loss (Rock solid) |
| SDM630-BVP | First SDM (~2m) | 88 | 150 | 147 | 3 | **2.00%** | 48.5ms | 🟢 Extremely Low Loss (<2%) |
| SDM630-GH | Middle SDM (~2.2m) | 88 | 150 | 147 | 3 | **2.00%** | 28.5ms | 🟢 Extremely Low Loss (<2%) |
| SDM630-HB | Last SDM (~2.4m) | 88 | 150 | 147 | 3 | **2.00%** | 44.6ms | 🟢 Extremely Low Loss (<2%) |
| MAGNA3-HP1 | Bus End (Unterminated Cut!) | 62 | 150 | 145 | 5 | **3.33%** | 49.2ms | 🟡 Minor Physical Loss (2-5%) |

---

## 10. Follow-Up: 20ms Conflict Time Gap & Cross-Device Overflow Tests

*Test Timestamp: 2026-10-01 07:57:36*  
**Waveshare Setting Change:** `RS485 Conflict Time Gap` lowered by user from `50ms` to `20ms`.

### A. MAGNA3 Under 20ms Conflict Time Gap (62 Registers, 20ms Turnaround)
| Metric | Old (50ms Gap) | New (20ms Gap) | Impact |
| :--- | :---: | :---: | :--- |
| **Success Rate** | 100.0% | **100.0%** | Stable |
| **Average RTT** | 103.5 ms | **27.5 ms** | 73% latency reduction |
| **P95 Latency** | 1,633.8 ms | **293.3 ms** | Spikes eliminated |
| **Max Latency** | 2,318.7 ms | **593.1 ms** | Safely below 2s HA timeout |
| **Spikes > 1.5s** | Frequent | **0/30** | Zero timeout risk |

### B. Cross-Device Payload Impact: Does MAGNA3 Response Flood SDM UARTs?
| Prior Query | Target SDM Query | Delay | Iterations | Target SDM Success | SDM Avg RTT | Observation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| THMB50 (2 regs, 9B) | SDM-GH (2 regs, 9B) | 20ms | 20 | **20/20 (100.0%)** | 7.7ms | Baseline clean switch |
| MAGNA3 (62 regs, 129B) | SDM-GH (2 regs, 9B) | 20ms | 20 | **20/20 (100.0%)** | 6.9ms | SDM survives |
| MAGNA3 (62 regs, 129B) | SDM-GH (88 regs, 181B) | 20ms | 20 | **20/20 (100.0%)** | 24.4ms | SDM survives |

### C. Full Interleaved Polling Under 20ms Conflict Time Gap
Cycling order: `THMB50 (2) -> SDM-BVP (88) -> SDM-GH (88) -> SDM-HB (88) -> MAGNA3 (62)` with 20ms inter-query delay.

| Device | Registers | Success Rate | Old (50ms Gap) | New (20ms Gap) | Result |
| :--- | :---: | :---: | :---: | :---: | :--- |
| THMB50 | 2 | **15/15 (100.0%)** | 12/12 (100%) | **15/15** | Maintained |
| SDM-BVP | 88 | **0/15 (0.0%)** | 0/12 (0%) | **0/15** | Bottlenecked by 88-reg read |
| SDM-GH | 88 | **3/15 (20.0%)** | 0/12 (0%) | **3/15** | Improved |
| SDM-HB | 88 | **0/15 (0.0%)** | 10/12 (83%) | **0/15** | Bottlenecked by 88-reg read |
| MAGNA3 | 62 | **7/15 (46.7%)** | 4/12 (33%) | **7/15** | Bottlenecked by 88-reg read |

---

## 11. Cross-Device Overflow Verification: 88-Register Read on MAGNA3

*Test Timestamp: 2026-10-01 08:15:17*

Testing whether forcing an 88-register (186-byte) and 100-register (210-byte) response from MAGNA3 induces failures on subsequent SDM queries.

| Prior MAGNA3 Query | MAGNA3 Wire Bytes | Target SDM-GH Query | Delay | Iterations | MAGNA3 OK | SDM-GH OK | SDM-GH Success Rate | Result |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| MAGNA3 Small (2 regs, 14B) | ~14 B | SDM-GH Small (2 regs) | 20ms | 20 | 20/20 | 20/20 | **100.0%** | Flawless |
| MAGNA3 Normal (62 regs, 134B) | ~134 B | SDM-GH Small (2 regs) | 20ms | 20 | 20/20 | 20/20 | **100.0%** | Flawless |
| MAGNA3 88-Reg (88 regs, 186B) | ~186 B | SDM-GH Small (2 regs) | 20ms | 20 | 18/20 | 20/20 | **100.0%** | Flawless |
| MAGNA3 88-Reg (88 regs, 186B) | ~186 B | SDM-GH 88-Reg (88 regs) | 20ms | 20 | 13/20 | 0/20 | **  0.0%** | Severe Failure |
| MAGNA3 100-Reg (100 regs, 210B) | ~210 B | SDM-GH Small (2 regs) | 20ms | 20 | 20/20 | 20/20 | **100.0%** | Flawless |

---

## 12. Delay Sweep on 88-Register Alternating Reads (SDM-GH <-> SDM-HB)

*Test Timestamp: 2026-10-01 08:44:13*

Testing whether increasing the inter-frame silence delay all the way up to 2.0 seconds allows 88-register (181-byte) alternating reads between different Eastron meters.

| Inter-Frame Delay | GH (ID 102) Success | HB (ID 101) Success | Total Success | Success Rate | Avg RTT (ms) | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **50 ms** | 2/8 | 1/8 | 3/16 | **18.8%** | 593.3 ms | Collapsed |
| **100 ms** | 1/8 | 0/8 | 1/16 | **6.2%** | 552.2 ms | Collapsed |
| **250 ms** | 0/8 | 3/8 | 3/16 | **18.8%** | 447.7 ms | Collapsed |
| **500 ms** | 2/8 | 2/8 | 4/16 | **25.0%** | 499.1 ms | Collapsed |
| **750 ms** | 3/8 | 1/8 | 4/16 | **25.0%** | 487.1 ms | Collapsed |
| **1000 ms** | 3/8 | 1/8 | 4/16 | **25.0%** | 377.1 ms | Collapsed |
| **1500 ms** | 2/8 | 3/8 | 5/16 | **31.2%** | 411.6 ms | Collapsed |
| **2000 ms** | 0/8 | 8/8 | 8/16 | **50.0%** | 514.2 ms | Lockout (GH 0/8, HB 8/8) |

---

## 13. Exact Register Count Threshold Sweep (Alternating GH <-> HB)

*Test Timestamp: 2026-10-01 08:50:00*  
*Inter-query delay:* 50ms

Finding the exact byte/register boundary where alternating queries between Eastron meters succeed vs. collapse.

| Register Count | Bytes on Wire | GH (ID 102) | HB (ID 101) | Total Success Rate | Status | Observation |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **10** | 25 B | 1/8 | 6/8 | **43.8%** | 🔴 Collapsed | Initial post-sweep socket recovery |
| **16** | 37 B | 0/8 | 0/8 | **0.0%** | 🔴 Collapsed | Unsynced |
| **20** | 45 B | 1/8 | 0/8 | **6.2%** | 🔴 Collapsed | Unsynced |
| **24** | 53 B | 2/8 | 1/8 | **18.8%** | 🔴 Collapsed | Unsynced |
| **30** | 65 B | 8/8 | 8/8 | **100.0%** | 🟢 **100% Stable** | **Flawless synchronization (Zero drops)** |
| **36** | 77 B | 4/8 | 2/8 | **37.5%** | 🔴 Collapsed | Sharp drop |
| **42** | 89 B | 1/8 | 0/8 | **6.2%** | 🔴 Collapsed | Collapsed |
| **48** | 101 B | 1/8 | 1/8 | **12.5%** | 🔴 Collapsed | Collapsed |
| **56** | 117 B | 1/8 | 3/8 | **25.0%** | 🔴 Collapsed | Collapsed |
| **64** | 133 B | 0/8 | 0/8 | **0.0%** | 🔴 Collapsed | Complete lockout |
| **72** | 149 B | 2/8 | 1/8 | **18.8%** | 🔴 Collapsed | Collapsed |
| **80** | 165 B | 0/8 | 0/8 | **0.0%** | 🔴 Collapsed | Complete lockout |
| **88** | 181 B | 1/8 | 1/8 | **12.5%** | 🔴 Collapsed | Collapsed (HA default group size) |

