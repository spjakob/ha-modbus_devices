import socket
import struct
import time
import select
import sys
import os

GATEWAY_HOST = "192.168.1.5"
GATEWAY_PORT = 502
REPORT_PATH = "/home/jakob/codestuff/ha-modbus_devices/docs/08_Bus_Stress_and_Timing_Analysis.md"

DEVICES = [
    {"name": "THMB50", "slave_id": 50, "fc": 4, "addr": 0, "count_small": 2, "count_large": 2},
    {"name": "SDM630-BVP", "slave_id": 103, "fc": 4, "addr": 0, "count_small": 2, "count_large": 88},
    {"name": "SDM630-GH", "slave_id": 102, "fc": 4, "addr": 0, "count_small": 2, "count_large": 88},
    {"name": "SDM630-HB", "slave_id": 101, "fc": 4, "addr": 0, "count_small": 2, "count_large": 88},
    {"name": "MAGNA3-HP1", "slave_id": 14, "fc": 4, "addr": 300, "count_small": 2, "count_large": 62},
]

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
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def drain_buffer(self):
        if not self.sock:
            return 0
        drained = 0
        while True:
            r, _, _ = select.select([self.sock], [], [], 0)
            if not r:
                break
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                drained += len(chunk)
            except Exception:
                break
        return drained

    def read_exact(self, n, timeout):
        self.sock.settimeout(timeout)
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Socket closed")
            data += chunk
        return data

    def execute(self, slave_id, fc, addr, count, reconnect=False):
        t0 = time.perf_counter()
        if reconnect or not self.sock:
            try:
                self.connect()
            except Exception as e:
                return False, (time.perf_counter() - t0) * 1000, f"ConnectFail: {e}", b""

        self.drain_buffer()
        self.tid = (self.tid + 1) & 0xFFFF
        req = struct.pack(">HHHBBHH", self.tid, 0, 6, slave_id, fc, addr, count)

        try:
            self.sock.sendall(req)
        except Exception as e:
            self.close()
            return False, (time.perf_counter() - t0) * 1000, f"SendFail: {e}", b""

        deadline = time.perf_counter() + self.timeout
        while True:
            rem = deadline - time.perf_counter()
            if rem <= 0:
                if reconnect: self.close()
                return False, (time.perf_counter() - t0) * 1000, "Timeout", b""

            try:
                mbap = self.read_exact(6, timeout=rem)
                resp_tid, pid, length = struct.unpack(">HHH", mbap)
                rem = deadline - time.perf_counter()
                if rem <= 0:
                    if reconnect: self.close()
                    return False, (time.perf_counter() - t0) * 1000, "TimeoutBody", b""

                body = self.read_exact(length, timeout=rem)
                if resp_tid != self.tid:
                    # Ignore late packet from previous transaction and continue waiting
                    continue

                rtt = (time.perf_counter() - t0) * 1000
                unit, resp_fc = body[0], body[1]
                if resp_fc & 0x80:
                    err_code = body[2] if len(body) > 2 else 0
                    if reconnect: self.close()
                    return False, rtt, f"ModbusEx_0x{err_code:02X}", b""

                if unit != slave_id:
                    if reconnect: self.close()
                    return False, rtt, f"UnitMismatch_{unit}_vs_{slave_id}", b""

                if reconnect: self.close()
                return True, rtt, "", body[3:]

            except socket.timeout:
                if reconnect: self.close()
                return False, (time.perf_counter() - t0) * 1000, "Timeout", b""
            except Exception as e:
                self.close()
                return False, (time.perf_counter() - t0) * 1000, f"ReadFail: {e}", b""

def log_print(msg, md_file=None):
    print(msg, flush=True)
    if md_file:
        md_file.write(msg + "\n")
        md_file.flush()

def run_suite():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    md = open(REPORT_PATH, "w")

    log_print("# RS485 Modbus Bus Stress & Timing Diagnostic Report\n", md)
    log_print(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}", md)
    log_print(f"**Target Gateway:** `{GATEWAY_HOST}:{GATEWAY_PORT}` (Waveshare Modbus TCP-to-RTU)", md)
    log_print("**Environment:** Isolated diagnostic run (Home Assistant Docker container STOPPED)\n", md)
    log_print("### Physical Topology Under Test", md)
    log_print("```", md)
    log_print("WAVESHARE (GW) -> THMB50 (ID 50) -> SDM-BVP (ID 103) -> SDM-GH (ID 102) -> SDM-HB (ID 101) -> MAGNA3 (ID 14) -> [CUT - Unterminated]", md)
    log_print("```\n", md)
    log_print("---\n", md)

    client = ModbusClient()

    # =========================================================================
    # TEST 1: Connection Architecture (Single Persistent vs Reconnect-Per-Request)
    # =========================================================================
    log_print("## 1. Connection Architecture: Persistent Socket vs. Reconnect-Per-Request\n", md)
    log_print("| Mode | Device | Iterations | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |", md)
    log_print("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |", md)

    for mode_name, reconnect in [("Persistent Socket", False), ("Reconnect Per Request", True)]:
        if not reconnect:
            client.connect()
        for dev in [DEVICES[0], DEVICES[2], DEVICES[4]]: # THMB50, SDM-GH, MAGNA3
            successes = 0
            rtts = []
            errors = {}
            for _ in range(15):
                ok, rtt, err, _ = client.execute(dev["slave_id"], dev["fc"], dev["addr"], dev["count_large"], reconnect=reconnect)
                if ok:
                    successes += 1
                    rtts.append(rtt)
                else:
                    errors[err] = errors.get(err, 0) + 1
                time.sleep(0.05)

            avg_rtt = f"{sum(rtts)/len(rtts):.1f}" if rtts else "N/A"
            min_rtt = f"{min(rtts):.1f}" if rtts else "N/A"
            max_rtt = f"{max(rtts):.1f}" if rtts else "N/A"
            err_str = ", ".join(f"{k}:{v}" for k, v in errors.items()) if errors else "None"
            log_print(f"| {mode_name} | {dev['name']} (ID {dev['slave_id']}) | 15 | {successes/15*100:.1f}% | {avg_rtt} | {min_rtt} | {max_rtt} | {err_str} |", md)

        if not reconnect:
            client.close()

    log_print("\n---\n", md)

    # =========================================================================
    # TEST 2: Single-Device Speed Limits (Per-Device Minimum Turnaround Delay)
    # =========================================================================
    log_print("## 2. Single-Device Baseline: Turnaround Delay Limits\n", md)
    log_print("Testing each device individually with consecutive requests to find minimum required inter-frame silence.\n", md)
    delays_single = [0.0, 0.01, 0.025, 0.05, 0.10, 0.20]

    for dev in DEVICES:
        log_print(f"### Device: {dev['name']} (Slave ID {dev['slave_id']}, {dev['count_large']} registers)", md)
        log_print("| Turnaround Delay | Success | Success Rate | Avg RTT (ms) | Min RTT (ms) | Max RTT (ms) | Errors |", md)
        log_print("| :---: | :---: | :---: | :---: | :---: | :---: | :--- |", md)

        client.connect()
        for d in delays_single:
            successes = 0
            rtts = []
            errors = {}
            for _ in range(20):
                ok, rtt, err, _ = client.execute(dev["slave_id"], dev["fc"], dev["addr"], dev["count_large"], reconnect=False)
                if ok:
                    successes += 1
                    rtts.append(rtt)
                else:
                    errors[err] = errors.get(err, 0) + 1
                time.sleep(d)

            avg_rtt = f"{sum(rtts)/len(rtts):.1f}" if rtts else "N/A"
            min_rtt = f"{min(rtts):.1f}" if rtts else "N/A"
            max_rtt = f"{max(rtts):.1f}" if rtts else "N/A"
            err_str = ", ".join(f"{k}:{v}" for k, v in errors.items()) if errors else "None"
            log_print(f"| {d*1000:5.1f} ms | {successes}/20 | {successes/20*100:5.1f}% | {avg_rtt} | {min_rtt} | {max_rtt} | {err_str} |", md)

        client.close()
        log_print("", md)

    log_print("---\n", md)

    # =========================================================================
    # TEST 3: Payload Size Sensitivity (Small vs Large Request)
    # =========================================================================
    log_print("## 3. Payload Size Sensitivity: Small (2 Regs) vs. Large (Full Group)\n", md)
    log_print("| Device | Payload Size | Registers | Success Rate | Avg RTT (ms) | Errors |", md)
    log_print("| :--- | :--- | :---: | :---: | :---: | :--- |", md)

    client.connect()
    for dev in DEVICES:
        for size_label, cnt in [("Small", dev["count_small"]), ("Large", dev["count_large"])]:
            successes = 0
            rtts = []
            errors = {}
            for _ in range(20):
                ok, rtt, err, _ = client.execute(dev["slave_id"], dev["fc"], dev["addr"], cnt, reconnect=False)
                if ok:
                    successes += 1
                    rtts.append(rtt)
                else:
                    errors[err] = errors.get(err, 0) + 1
                time.sleep(0.05)

            avg_rtt = f"{sum(rtts)/len(rtts):.1f}" if rtts else "N/A"
            err_str = ", ".join(f"{k}:{v}" for k, v in errors.items()) if errors else "None"
            log_print(f"| {dev['name']} (ID {dev['slave_id']}) | {size_label} | {cnt} | {successes/20*100:5.1f}% | {avg_rtt} | {err_str} |", md)
    client.close()

    log_print("\n---\n", md)

    # =========================================================================
    # TEST 4: Interleaved Polling & ID Switching Limits (The Real Bus Stress)
    # =========================================================================
    log_print("## 4. Multi-Device Interleaved Polling (Cycling All 5 Devices)\n", md)
    log_print("Simulating real coordinator polling: `THMB50 -> SDM-BVP -> SDM-GH -> SDM-HB -> MAGNA3 -> ...`\n", md)
    delays_interleaved = [0.0, 0.02, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30]

    log_print("| Turnaround Delay | Overall Success | THMB50 (50) | SDM-BVP (103) | SDM-GH (102) | SDM-HB (101) | MAGNA3 (14) | Dominant Error |", md)
    log_print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |", md)

    for d in delays_interleaved:
        client.connect()
        dev_success = {dev["name"]: 0 for dev in DEVICES}
        dev_total = {dev["name"]: 0 for dev in DEVICES}
        all_errors = {}
        CYCLES = 12

        for _ in range(CYCLES):
            for dev in DEVICES:
                ok, rtt, err, _ = client.execute(dev["slave_id"], dev["fc"], dev["addr"], dev["count_large"], reconnect=False)
                dev_total[dev["name"]] += 1
                if ok:
                    dev_success[dev["name"]] += 1
                else:
                    all_errors[err] = all_errors.get(err, 0) + 1
                time.sleep(d)

        client.close()

        total_reqs = sum(dev_total.values())
        total_ok = sum(dev_success.values())
        overall_pct = total_ok / total_reqs * 100
        p_50 = f"{dev_success['THMB50']}/{dev_total['THMB50']}"
        p_103 = f"{dev_success['SDM630-BVP']}/{dev_total['SDM630-BVP']}"
        p_102 = f"{dev_success['SDM630-GH']}/{dev_total['SDM630-GH']}"
        p_101 = f"{dev_success['SDM630-HB']}/{dev_total['SDM630-HB']}"
        p_14 = f"{dev_success['MAGNA3-HP1']}/{dev_total['MAGNA3-HP1']}"
        dom_err = sorted(all_errors.items(), key=lambda x: x[1], reverse=True)[0][0] if all_errors else "None"

        log_print(f"| {d*1000:5.1f} ms | {total_ok}/{total_reqs} ({overall_pct:5.1f}%) | {p_50} | {p_103} | {p_102} | {p_101} | {p_14} | {dom_err} |", md)

    log_print("\n---\n", md)

    # =========================================================================
    # TEST 5: Targeted Follow-up: Gateway Flush Behavior
    # =========================================================================
    log_print("## 5. Gateway Behavior: Same-Device vs Different-Device Rapid Switching\n", md)
    log_print("Testing whether the bottleneck is pure inter-frame silence OR specifically changing Slave IDs.\n", md)
    log_print("| Test Condition | Delay | Success Rate | Details |", md)
    log_print("| :--- | :---: | :---: | :--- |", md)

    # Condition A: 30 consecutive requests to SDM-GH with 20ms delay
    client.connect()
    ok_a = sum(1 for _ in range(30) if client.execute(102, 4, 0, 88)[0] and not time.sleep(0.02))
    client.close()
    log_print(f"| 30x SDM-GH Only (Same Slave ID) | 20 ms | {ok_a/30*100:.1f}% | {ok_a}/30 successful |", md)

    # Condition B: Alternating SDM-GH and SDM-HB with 20ms delay
    client.connect()
    ok_b = 0
    for _ in range(15):
        if client.execute(102, 4, 0, 88)[0]: ok_b += 1
        time.sleep(0.02)
        if client.execute(101, 4, 0, 88)[0]: ok_b += 1
        time.sleep(0.02)
    client.close()
    log_print(f"| Alternating GH <-> HB (Switching IDs) | 20 ms | {ok_b/30*100:.1f}% | {ok_b}/30 successful |", md)

    # Condition C: Alternating SDM-GH and SDM-HB with 100ms delay
    client.connect()
    ok_c = 0
    for _ in range(15):
        if client.execute(102, 4, 0, 88)[0]: ok_c += 1
        time.sleep(0.10)
        if client.execute(101, 4, 0, 88)[0]: ok_c += 1
        time.sleep(0.10)
    client.close()
    log_print(f"| Alternating GH <-> HB (Switching IDs) | 100 ms | {ok_c/30*100:.1f}% | {ok_c}/30 successful |", md)

    # Condition D: Alternating SDM-GH and SDM-HB with 200ms delay
    client.connect()
    ok_d = 0
    for _ in range(15):
        if client.execute(102, 4, 0, 88)[0]: ok_d += 1
        time.sleep(0.20)
        if client.execute(101, 4, 0, 88)[0]: ok_d += 1
        time.sleep(0.20)
    client.close()
    log_print(f"| Alternating GH <-> HB (Switching IDs) | 200 ms | {ok_d/30*100:.1f}% | {ok_d}/30 successful |", md)

    log_print("\n---\n", md)
    log_print("## 6. Summary of Empirical Findings & Proposed Solution\n", md)
    log_print("*(Automated diagnostic complete - see analysis section below)*\n", md)

    md.close()
    print("\nInvestigation completed. Full report saved to:", REPORT_PATH)

if __name__ == "__main__":
    run_suite()
