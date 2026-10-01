import socket
import struct
import time
import select
import statistics
import os

GATEWAY_HOST = "192.168.1.5"
GATEWAY_PORT = 502
REPORT_PATH = "/home/jakob/codestuff/ha-modbus_devices/docs/08_Bus_Stress_and_Timing_Analysis.md"

DEVICES = [
    {"name": "THMB50", "slave_id": 50, "fc": 4, "addr": 0, "full_count": 2},
    {"name": "SDM630-BVP", "slave_id": 103, "fc": 4, "addr": 0, "full_count": 88},
    {"name": "SDM630-GH", "slave_id": 102, "fc": 4, "addr": 0, "full_count": 88},
    {"name": "SDM630-HB", "slave_id": 101, "fc": 4, "addr": 0, "full_count": 88},
    {"name": "MAGNA3-HP1", "slave_id": 14, "fc": 4, "addr": 300, "full_count": 62},
]

class BusQualityTester:
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

    def query(self, slave_id, fc, addr, count):
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
                    continue  # Ghost packet

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

def test_bus_quality():
    tester = BusQualityTester()
    tester.connect()

    report_lines = []
    report_lines.append("\n---\n")
    report_lines.append("## 9. Comprehensive Bus Quality Benchmark Per Device\n")
    report_lines.append("Each device was tested with 50 consecutive queries under its native payload size, with 50ms inter-query silence.\n")
    report_lines.append("| Device | Slave ID | Registers | Tests | Success Rate | Min RTT | Avg RTT | Median | P95 RTT | Max RTT | Jitter (StdDev) | Signal Health Rating |")
    report_lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

    print("\n" + "="*80)
    print("STARTING INDIVIDUAL BUS QUALITY BENCHMARK (50 queries per device)")
    print("="*80)

    for dev in DEVICES:
        name = dev["name"]
        sid = dev["slave_id"]
        fc = dev["fc"]
        addr = dev["addr"]
        cnt = dev["full_count"]

        successes = 0
        rtts = []
        errors = {}

        N = 50
        print(f"\nTesting {name} (Slave {sid}, {cnt} registers)...", flush=True)

        for i in range(N):
            ok, rtt, err = tester.query(sid, fc, addr, cnt)
            if ok:
                successes += 1
                rtts.append(rtt)
            else:
                errors[err] = errors.get(err, 0) + 1
            time.sleep(0.05)

        succ_pct = (successes / N) * 100
        min_rtt = min(rtts) if rtts else 0
        avg_rtt = statistics.mean(rtts) if rtts else 0
        med_rtt = statistics.median(rtts) if rtts else 0
        p95_rtt = statistics.quantiles(rtts, n=20)[18] if len(rtts) >= 20 else max(rtts) if rtts else 0
        max_rtt = max(rtts) if rtts else 0
        std_dev = statistics.stdev(rtts) if len(rtts) > 1 else 0

        # Health rating logic
        if succ_pct >= 98 and std_dev < 30:
            health = "🟢 Excellent (Clean line)"
        elif succ_pct >= 90 and std_dev < 100:
            health = "🟡 Good (Minor noise/jitter)"
        elif succ_pct >= 75:
            health = "🟠 Fair (Moderate interference)"
        else:
            health = "🔴 Poor (Severe packet loss / noise)"

        row = (f"| {name} | {sid} | {cnt} | {N} | {succ_pct:5.1f}% | {min_rtt:5.1f}ms | {avg_rtt:5.1f}ms | "
               f"{med_rtt:5.1f}ms | {p95_rtt:5.1f}ms | {max_rtt:5.1f}ms | ±{std_dev:4.1f}ms | {health} |")
        report_lines.append(row)
        print(f"-> {name}: {succ_pct:.1f}% success, Avg: {avg_rtt:.1f}ms (Min: {min_rtt:.1f}, Max: {max_rtt:.1f}), Jitter: ±{std_dev:.1f}ms -> {health}")
        if errors:
            print(f"   Errors encountered: {errors}")

    # =========================================================================
    # SPECIAL TARGETED TEST FOR MAGNA3: Small vs Full Register Sets & Rapid Queries
    # =========================================================================
    report_lines.append("\n### Deep Dive: MAGNA3 Signal & Responsiveness Profile\n")
    report_lines.append("Testing MAGNA3 with varying register count (2, 10, 30, 62) and turnaround delays to isolate its failure profile.\n")
    report_lines.append("| Register Count | Total Bytes | Delay | Success Rate | Avg RTT | P95 RTT | Max RTT | Errors | Notes |")
    report_lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |")

    print("\n" + "="*80)
    print("STARTING MAGNA3 DEEP DIVE (Evaluating payload sizes and delays)")
    print("="*80)

    for cnt in [2, 10, 30, 62]:
        for d in [0.02, 0.10]:
            successes = 0
            rtts = []
            errors = {}
            M = 25
            bytes_on_wire = 5 + (cnt * 2)

            for _ in range(M):
                ok, rtt, err = tester.query(14, 4, 300, cnt)
                if ok:
                    successes += 1
                    rtts.append(rtt)
                else:
                    errors[err] = errors.get(err, 0) + 1
                time.sleep(d)

            succ_pct = (successes / M) * 100
            avg_r = statistics.mean(rtts) if rtts else 0
            p95_r = statistics.quantiles(rtts, n=20)[18] if len(rtts) >= 20 else max(rtts) if rtts else 0
            max_r = max(rtts) if rtts else 0
            err_str = ", ".join(f"{k}:{v}" for k, v in errors.items()) if errors else "None"

            note = "Normal" if succ_pct == 100 else "Instability observed"
            row = f"| {cnt} | {bytes_on_wire} B | {d*1000:4.0f}ms | {succ_pct:5.1f}% | {avg_r:5.1f}ms | {p95_r:5.1f}ms | {max_r:5.1f}ms | {err_str} | {note} |"
            report_lines.append(row)
            print(f"MAGNA3 count={cnt:2d}, delay={d*1000:3.0f}ms: {succ_pct:5.1f}% success, Avg: {avg_r:5.1f}ms, P95: {p95_r:5.1f}ms, Max: {max_r:5.1f}ms | Errors: {err_str}")

    tester.close()

    # Append to markdown file
    with open(REPORT_PATH, "a") as f:
        f.write("\n".join(report_lines) + "\n")
    print(f"\nBenchmark completed and appended to {REPORT_PATH}")

if __name__ == "__main__":
    test_bus_quality()
