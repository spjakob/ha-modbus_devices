import socket
import struct
import time
import select
import statistics

GATEWAY_HOST = "192.168.1.5"
GATEWAY_PORT = 502
REPORT_PATH = "/home/jakob/codestuff/ha-modbus_devices/docs/08_Bus_Stress_and_Timing_Analysis.md"

class ModbusClient:
    def __init__(self, host=GATEWAY_HOST, port=GATEWAY_PORT, timeout=2.5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.tid = 0

    def connect(self):
        self.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((self.host, self.port))

    def close(self):
        if self.sock:
            try: self.sock.close()
            except Exception: pass
            self.sock = None

    def drain(self):
        if not self.sock: return 0
        drained = 0
        while True:
            r, _, _ = select.select([self.sock], [], [], 0)
            if not r: break
            try:
                c = self.sock.recv(4096)
                if not c: break
                drained += len(c)
            except Exception: break
        return drained

    def read_exact(self, n, timeout):
        self.sock.settimeout(timeout)
        buf = b""
        while len(buf) < n:
            c = self.sock.recv(n - len(buf))
            if not c: raise ConnectionError("Closed")
            buf += c
        return buf

    def execute(self, slave_id, fc, addr, count):
        t0 = time.perf_counter()
        if not self.sock:
            self.connect()

        self.drain()
        self.tid = (self.tid + 1) & 0xFFFF
        req = struct.pack(">HHHBBHH", self.tid, 0, 6, slave_id, fc, addr, count)

        try:
            self.sock.sendall(req)
        except Exception as e:
            self.close()
            return False, (time.perf_counter() - t0)*1000, f"SendErr: {e}"

        deadline = time.perf_counter() + self.timeout
        while True:
            rem = deadline - time.perf_counter()
            if rem <= 0:
                return False, (time.perf_counter() - t0)*1000, "Timeout"

            try:
                mbap = self.read_exact(6, timeout=rem)
                resp_tid, pid, length = struct.unpack(">HHH", mbap)
                rem = deadline - time.perf_counter()
                if rem <= 0:
                    return False, (time.perf_counter() - t0)*1000, "Timeout"

                body = self.read_exact(length, timeout=rem)
                if resp_tid != self.tid:
                    continue

                rtt = (time.perf_counter() - t0)*1000
                unit, resp_fc = body[0], body[1]

                if resp_fc & 0x80:
                    err_c = body[2] if len(body) > 2 else 0
                    return False, rtt, f"ModbusEx_{err_c:02X}"

                if unit != slave_id:
                    return False, rtt, f"UnitMismatch_{unit}"

                return True, rtt, ""
            except socket.timeout:
                return False, (time.perf_counter() - t0)*1000, "Timeout"
            except Exception as e:
                self.close()
                return False, (time.perf_counter() - t0)*1000, f"RecvErr: {e}"

def run_tests():
    client = ModbusClient()
    client.connect()

    report_lines = []
    report_lines.append("\n---\n")
    report_lines.append("## 11. Follow-Up: 20ms Conflict Time Gap & Cross-Device Overflow Tests\n")
    report_lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')} (HA Stopped)\n")
    report_lines.append("**Waveshare Setting Change:** `RS485 Conflict Time Gap` lowered from `50ms` to `20ms`.\n")

    print("\n" + "="*80)
    print("TEST 1: MAGNA3 RESPONSE PROFILE UNDER 20ms CONFLICT GAP (30 queries)")
    print("="*80)

    # Test MAGNA3 (62 registers) at 20ms delay
    rtts_magna = []
    succ_magna = 0
    spikes_magna = 0
    N = 30
    for _ in range(N):
        ok, rtt, err = client.execute(14, 4, 300, 62)
        if ok:
            succ_magna += 1
            rtts_magna.append(rtt)
            if rtt > 1500: spikes_magna += 1
        time.sleep(0.02)

    avg_m = statistics.mean(rtts_magna) if rtts_magna else 0
    min_m = min(rtts_magna) if rtts_magna else 0
    p95_m = statistics.quantiles(rtts_magna, n=20)[18] if len(rtts_magna) >= 20 else max(rtts_magna) if rtts_magna else 0
    max_m = max(rtts_magna) if rtts_magna else 0

    print(f"MAGNA3 62-reg (20ms delay): {succ_magna}/{N} ({succ_magna/N*100:.1f}%), Avg: {avg_m:.1f}ms, P95: {p95_m:.1f}ms, Max: {max_m:.1f}ms, Spikes>1.5s: {spikes_magna}")

    report_lines.append("### A. MAGNA3 Under 20ms Conflict Time Gap (62 Registers, 20ms Turnaround)\n")
    report_lines.append("| Metric | Old (50ms Gap) | New (20ms Gap) | Impact |")
    report_lines.append("| :--- | :---: | :---: | :--- |")
    report_lines.append(f"| **Success Rate** | 100.0% | **{succ_magna/N*100:.1f}%** | {'Stable' if succ_magna == N else 'Dropped packets'} |")
    report_lines.append(f"| **Average RTT** | 103.5 ms | **{avg_m:.1f} ms** | {'Improved' if avg_m < 103.5 else 'Unchanged'} |")
    report_lines.append(f"| **P95 Latency** | 1,633.8 ms | **{p95_m:.1f} ms** | {'Significantly improved' if p95_m < 500 else 'High jitter'} |")
    report_lines.append(f"| **Max Latency** | 2,318.7 ms | **{max_m:.1f} ms** | {'Below 2s HA timeout!' if max_m < 2000 else 'Exceeds 2s timeout'} |")
    report_lines.append(f"| **Spikes > 1.5s** | High | **{spikes_magna}/{N}** | {'Zero spikes!' if spikes_magna == 0 else 'Spikes present'} |\n")

    # =========================================================================
    # TEST 2: Cross-Device Long Read Overflow Test (Does MAGNA3 long read affect SDM?)
    # =========================================================================
    print("\n" + "="*80)
    print("TEST 2: DOES A LONG READ FROM MAGNA3 AFFECT SUBSEQUENT SDM READS?")
    print("="*80)

    report_lines.append("### B. Cross-Device Payload Impact: Does MAGNA3 Response Flood SDM UARTs?\n")
    report_lines.append("| Prior Query | Target SDM Query | Delay | Iterations | Target SDM Success | SDM Avg RTT | Observation |")
    report_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |")

    M = 20

    # Case 1: Small THMB50 (2 regs) -> SDM-GH (2 regs)
    ok_sdm1 = 0
    rtts_sdm1 = []
    for _ in range(M):
        client.execute(50, 4, 0, 2)
        time.sleep(0.02)
        ok, rtt, _ = client.execute(102, 4, 0, 2)
        if ok: ok_sdm1 += 1; rtts_sdm1.append(rtt)
        time.sleep(0.02)
    avg1 = f"{statistics.mean(rtts_sdm1):.1f}ms" if rtts_sdm1 else "N/A"
    print(f"Case 1 (THMB50 2 regs -> SDM-GH 2 regs): SDM Success = {ok_sdm1}/{M} ({ok_sdm1/M*100:.1f}%)")
    report_lines.append(f"| THMB50 (2 regs, 9B) | SDM-GH (2 regs, 9B) | 20ms | {M} | **{ok_sdm1}/{M} ({ok_sdm1/M*100:.1f}%)** | {avg1} | Baseline clean switch |")

    # Case 2: Large MAGNA3 (62 regs) -> SDM-GH (2 regs)
    ok_sdm2 = 0
    rtts_sdm2 = []
    for _ in range(M):
        client.execute(14, 4, 300, 62)
        time.sleep(0.02)
        ok, rtt, _ = client.execute(102, 4, 0, 2)
        if ok: ok_sdm2 += 1; rtts_sdm2.append(rtt)
        time.sleep(0.02)
    avg2 = f"{statistics.mean(rtts_sdm2):.1f}ms" if rtts_sdm2 else "N/A"
    print(f"Case 2 (MAGNA3 62 regs -> SDM-GH 2 regs): SDM Success = {ok_sdm2}/{M} ({ok_sdm2/M*100:.1f}%)")
    report_lines.append(f"| MAGNA3 (62 regs, 129B) | SDM-GH (2 regs, 9B) | 20ms | {M} | **{ok_sdm2}/{M} ({ok_sdm2/M*100:.1f}%)** | {avg2} | {'SDM survives' if ok_sdm2 == M else 'SDM affected by MAGNA payload!'} |")

    # Case 3: Large MAGNA3 (62 regs) -> SDM-GH (88 regs)
    ok_sdm3 = 0
    rtts_sdm3 = []
    for _ in range(M):
        client.execute(14, 4, 300, 62)
        time.sleep(0.02)
        ok, rtt, _ = client.execute(102, 4, 0, 88)
        if ok: ok_sdm3 += 1; rtts_sdm3.append(rtt)
        time.sleep(0.02)
    avg3 = f"{statistics.mean(rtts_sdm3):.1f}ms" if rtts_sdm3 else "N/A"
    print(f"Case 3 (MAGNA3 62 regs -> SDM-GH 88 regs): SDM Success = {ok_sdm3}/{M} ({ok_sdm3/M*100:.1f}%)")
    report_lines.append(f"| MAGNA3 (62 regs, 129B) | SDM-GH (88 regs, 181B) | 20ms | {M} | **{ok_sdm3}/{M} ({ok_sdm3/M*100:.1f}%)** | {avg3} | {'SDM survives' if ok_sdm3 == M else 'SDM fails! Overrun confirmed.'} |\n")

    # =========================================================================
    # TEST 3: Interleaved Multi-Device Cycling Under 20ms Conflict Gap
    # =========================================================================
    print("\n" + "="*80)
    print("TEST 3: FULL INTERLEAVED CYCLING (15 cycles across all 5 devices)")
    print("="*80)

    devices = [
        ("THMB50", 50, 4, 0, 2),
        ("SDM-BVP", 103, 4, 0, 88),
        ("SDM-GH", 102, 4, 0, 88),
        ("SDM-HB", 101, 4, 0, 88),
        ("MAGNA3", 14, 4, 300, 62),
    ]

    CYCLES = 15
    res = {d[0]: 0 for d in devices}
    for _ in range(CYCLES):
        for name, sid, fc, addr, cnt in devices:
            ok, rtt, _ = client.execute(sid, fc, addr, cnt)
            if ok: res[name] += 1
            time.sleep(0.02)

    print("Interleaved Results (20ms gap):", res)

    report_lines.append("### C. Full Interleaved Polling Under 20ms Conflict Time Gap\n")
    report_lines.append("Cycling order: `THMB50 (2) -> SDM-BVP (88) -> SDM-GH (88) -> SDM-HB (88) -> MAGNA3 (62)` with 20ms inter-query delay.\n")
    report_lines.append("| Device | Registers | Success Rate | Old (50ms Gap) | New (20ms Gap) | Result |")
    report_lines.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

    for name, sid, fc, addr, cnt in devices:
        s = res[name]
        pct = (s / CYCLES) * 100
        old_val = "12/12 (100%)" if name == "THMB50" else ("0/12 (0%)" if "BVP" in name or "GH" in name else ("10/12 (83%)" if "HB" in name else "4/12 (33%)"))
        report_lines.append(f"| {name} | {cnt} | **{s}/{CYCLES} ({pct:.1f}%)** | {old_val} | **{s}/{CYCLES}** | {'Improved' if s > 0 and '0/' in old_val else ('Maintained' if pct >= 80 else 'Still bottlenecked by 88-reg read')} |")

    client.close()

    with open(REPORT_PATH, "a") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\nAll tests completed and appended to {REPORT_PATH}")

if __name__ == "__main__":
    run_tests()
