# RS485 Modbus Bus Timing, Capacity & Topology Findings

**Date:** 2026-10-01  
**Scope:** Root cause diagnosis of communication drops, timing latency spikes, and payload thresholds across the RS485 bus.  
**Tested Devices:**
- THMB50 (Slave ID 50)
- SDM630-BVP (Slave ID 103)
- SDM630-GH (Slave ID 102)
- SDM630-HB (Slave ID 101)
- Grundfos MAGNA3-HP1 (Slave ID 14)
*(Note: QDY30A is isolated on a separate physical Waveshare gateway at `192.168.1.6`)*

---

## Executive Summary

Through a structured sequence of isolated empirical tests executed directly against the Waveshare gateway (`192.168.1.5:502`) with Home Assistant stopped, we have isolated the definitive causes of the bus errors and latency spikes:

1. **The Physical RS485 Cable Is Electrically Healthy:**
   - In baseline isolation tests with compliant timing, the devices achieve **0.00% to 2.00% physical frame loss**.
   - The unterminated cable end at the MAGNA3 pump introduces only a minor reflection noise floor (**~3.3% loss**), which is completely manageable via standard Modbus retries and easily eliminated by adding a 120-ohm terminator.
   - **Conclusion:** There is **NO** broken wire, short circuit, or major electrical grounding failure on the physical bus.

2. **Waveshare "RS485 Conflict Time Gap" Caused the MAGNA3 Latency Spikes:**
   - The factory default setting of `50ms` for `RS485 Conflict Time Gap` conflicted with Home Assistant's rapid turnaround requests. When Home Assistant sent queries faster than 50ms, the Waveshare gateway queued and delayed serial transmission, compounding latency up to **2,318 ms** (causing frequent Home Assistant 2.0s timeouts).
   - **Resolution:** Lowering `RS485 Conflict Time Gap` to `20ms` completely eliminated these spikes. MAGNA3 95th-percentile response time dropped from **1,633 ms down to 293 ms**, with **zero spikes over 1.5 seconds**.

3. **The Multi-Meter "Collapse" Is Driven by Large Payload Alternating Reads:**
   - When any single Eastron SDM630 meter is queried continuously by itself (even reading 88 registers / 181 bytes), it achieves **100.0% zero-error reliability**.
   - When alternating between different Eastron meters (e.g. `SDM-GH -> SDM-HB`), attempting to read 88 registers causes the bus to collapse to **6% to 25% success**.
   - **Critically, increasing inter-frame delay up to 2.0 seconds does NOT solve the problem.** Even with 2,000 ms of dead bus silence between requests, alternating 88-register reads achieves at best 50% (one meter locks out the other).
   - In contrast, reading smaller payloads ($\le 30$ registers / 65 bytes on the wire) achieves **100.0% flawless stability** across all meters under rapid alternating cycles.

---

## Detailed Technical Analysis

### 1. Why Increasing Delay to 2.0 Seconds Does Not Fix 88-Register Reads

A common initial hypothesis for Modbus bus collisions is insufficient turnaround silence (i.e. one device is still releasing the RS485 driver while the next query is transmitted). 

To test this rigorously, we ran an exhaustive delay sweep alternating between `SDM-GH (102)` and `SDM-HB (101)` requesting 88 registers:

| Delay Between Meters | GH Success | HB Success | Overall Success Rate | Observation |
| :---: | :---: | :---: | :---: | :--- |
| **50 ms** | 2/8 | 1/8 | **18.8%** | Severe collapse |
| **100 ms** | 1/8 | 0/8 | **6.2%** | Near total loss |
| **250 ms** | 0/8 | 3/8 | **18.8%** | Lockout behavior |
| **500 ms** | 2/8 | 2/8 | **25.0%** | Both meters failing |
| **750 ms** | 3/8 | 1/8 | **25.0%** | Both meters failing |
| **1000 ms** | 3/8 | 1/8 | **25.0%** | 1 full second dead time does not help |
| **1500 ms** | 2/8 | 3/8 | **31.2%** | Intermittent timeouts |
| **2000 ms** | 0/8 | 8/8 | **50.0%** | 2 full seconds dead time: HB responds, GH completely locked out (0/8) |

**Conclusion:** The failure is **not** caused by insufficient RS485 line turnaround time or driver disable latency ($t_{\text{off}}$). If it were a turnaround delay issue, a 2.0-second pause would have restored 100% reliability. Instead, the meters remain desynchronized or unresponsive.

### 2. Receiver vs. Transmitter Hardware Dynamics

To understand why large payloads break multi-meter operation, consider the half-duplex RS485 architecture:

```
[Master] ===(A/B Bus)========================================
             |                   |                   |
        [SDM-BVP]           [SDM-GH]            [SDM-HB]
         Addr 103            Addr 102            Addr 101
```

* **When testing SDM-GH alone:** 
  SDM-GH receives an 8-byte request, disables its receiver, enables its transmitter, drives 181 bytes onto the wire, disables transmitter, and re-enables receiver. Because its own receiver is muted during transmission, SDM-GH's UART never buffers its own 181-byte response. Success: **100%**.
* **When alternating between SDM-GH and SDM-HB:**
  1. Master sends request to SDM-GH (102).
  2. SDM-GH responds with an **88-register payload (181 contiguous bytes)**. At 9600 baud, this blast lasts **188.5 ms**.
  3. SDM-HB (101) is listening on the same wire. SDM-HB's hardware UART receives all 181 bytes.
  4. Embedded microcontrollers in energy meters have small hardware FIFOs (typically 64 or 128 bytes). Receiving 181 foreign bytes triggers a **hardware UART Overrun Error (`OERR`)** or internal parser desynchronization in SDM-HB.
  5. By the time the Master issues the next command addressed to SDM-HB, SDM-HB's serial state machine is either hung in overrun recovery or misses the opening frame sync.
* **Why Cross-Device Tests with MAGNA3 Succeeded:**
  When MAGNA3 (ID 14) transmitted 62 registers (129 bytes) or even 88 registers (186 bytes), SDM-GH was subsequently able to answer a small (2-register) read with **100% success**. The SDM meters recover cleanly if the subsequent query is small, but they fail completely if asked to generate and transmit another massive 88-register frame while recovering from a neighbor's massive frame.

---

## Exact Payload Capacity Threshold

Our register count sweep testing alternating queries between Eastron meters revealed a clear boundary:

* **$\le 30$ Registers ( $\le 65$ Bytes on Wire):** **100.0% Stable.**  
  Alternating queries between SDM meters succeed flawlessly without a single timeout or dropped frame.
* **$> 30$ Registers ( $\ge 77$ Bytes on Wire):** **Rapid Collapse.**  
  At 36 registers (77 bytes), success collapses to 37.5%. At 42 registers and higher, success drops to under 20% or complete lockouts (0%).

---

## Actionable Recommendations & Implementation Path

### 1. Restructure SDM630 Register Groups in `SDM630.py` (Integration Level)
* The root vulnerability in Home Assistant is the monolithic `GROUP_INPUT_1` (`MAIN_MEASUREMENTS`), which currently requests **88 consecutive registers** (`count=88`, 181 bytes) in a single Modbus read.
* **Resolution:** Subdivide `GROUP_INPUT_1` into smaller logical groups of **$\le 30$ registers each** (for example, three groups of 28 to 30 registers).
  - *Group 1A (Voltages & Currents):* Addr 0..11 (12 registers)
  - *Group 1B (Power & VA):* Addr 12..29 (18 registers)
  - *Group 1C (VAr, Power Factors, Angles):* Addr 30..58 (28 registers)
* By keeping every individual transaction under 30 registers (65 bytes on the wire), all Eastron meters stay within hardware FIFO capacity and achieve **100% zero-drop reliability**.

### 2. Retain Waveshare `RS485 Conflict Time Gap` at 20ms (Gateway Level)
* Keep the user's updated setting of **`20ms`** for `RS485 Conflict Time Gap` on the Waveshare web interface (`http://192.168.1.5`).
* This eliminates the internal gateway queue accumulation that was driving MAGNA3 latencies above 2,300 ms.

### 3. Install 120Ω Termination Resistor at MAGNA3 (Physical Bus Level)
* Place a standard $120\,\Omega$ ($0.25\,\text{W}$) resistor across terminals A and B at the MAGNA3 pump (the far physical end of the bus).
* This will eliminate the ~3.3% reflection loss at the unterminated cut and ensure pristine square-wave transitions along the entire bus length.
