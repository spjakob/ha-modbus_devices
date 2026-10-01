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
            return False, (time.perf_counter() - t0)*1000, f"SendErr: {e}", 0

        deadline = time.perf_counter() + self.timeout
        while True:
            rem = deadline - time.perf_counter()
            if rem <= 0:
                return False, (time.perf_counter() - t0)*1000, "Timeout", 0

            try:
                mbap = self.read_exact(6, timeout=rem)
                resp_tid, pid, length = struct.unpack(">HHH", mbap)
                rem = deadline - time.perf_counter()
                if rem <= 0:
                    return False, (time.perf_counter() - t0)*1000, "Timeout", 0

                body = self.read_exact(length, timeout=rem)
                if resp_tid != self.tid:
                    continue

                rtt = (time.perf_counter() - t0)*1000
                unit, resp_fc = body[0], body[1]

                if resp_fc & 0x80:
                    err_c = body[2] if len(body) > 2 else 0
                    return False, rtt, f"ModbusEx_{err_c:02X}", len(body)

                if unit != slave_id:
                    return False, rtt, f"UnitMismatch_{unit}", len(body)

                return True, rtt, "", len(body)
            except socket.timeout:
                return False, (time.perf_counter() - t0)*1000, "Timeout", 0
            except Exception as e:
                self.close()
                return False, (time.perf_counter() - t0)*1000, f"RecvErr: {e}", 0

def run_test():
    client = ModbusClient()
    client.connect()

    report_lines = []
    report_lines.append("\n---\n")
    report_lines.append("## 12. Cross-Device Overflow Verification: 88-Register Read on MAGNA3\n")
    report_lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')} (HA Stopped)\n")
    report_lines.append("Testing whether forcing an 88-register (186-byte) and 100-register (210-byte) response from MAGNA3 induces failures on subsequent SDM queries.\n")

    print("\n" + "="*80)
    print("VERIFYING MAGNA3 88-REGISTER READ IMPACT ON SDM-GH")
    print("="*80)

    # Condition 1: Baseline Small MAGNA3 (2 regs, FC4 addr 300) -> SDM-GH (2 regs, FC4 addr 0)
    # Condition 2: Full MAGNA3 Default (62 regs, FC4 addr 300) -> SDM-GH (2 regs, FC4 addr 0)
    # Condition 3: Large MAGNA3 (88 regs, FC3 addr 0) -> SDM-GH (2 regs, FC4 addr 0)
    # Condition 4: Large MAGNA3 (88 regs, FC3 addr 0) -> SDM-GH (88 regs, FC4 addr 0)
    # Condition 5: Huge MAGNA3 (100 regs, FC4 addr 300) -> SDM-GH (2 regs, FC4 addr 0)

    conditions = [
        ("MAGNA3 Small (2 regs, 14B)", 14, 4, 300, 2, "SDM-GH Small (2 regs)", 102, 4, 0, 2),
        ("MAGNA3 Normal (62 regs, 134B)", 14, 4, 300, 62, "SDM-GH Small (2 regs)", 102, 4, 0, 2),
        ("MAGNA3 88-Reg (88 regs, 186B)", 14, 3, 0, 88, "SDM-GH Small (2 regs)", 102, 4, 0, 2),
        ("MAGNA3 88-Reg (88 regs, 186B)", 14, 3, 0, 88, "SDM-GH 88-Reg (88 regs)", 102, 4, 0, 88),
        ("MAGNA3 100-Reg (100 regs, 210B)", 14, 4, 300, 100, "SDM-GH Small (2 regs)", 102, 4, 0, 2),
    ]

    report_lines.append("| Prior MAGNA3 Query | MAGNA3 Wire Bytes | Target SDM-GH Query | Delay | Iterations | MAGNA3 OK | SDM-GH OK | SDM-GH Success Rate | Result |")
    report_lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")

    N = 20
    for label_m, m_sid, m_fc, m_addr, m_cnt, label_s, s_sid, s_fc, s_addr, s_cnt in conditions:
        ok_m = 0
        ok_s = 0
        bytes_m = 0
        rtts_s = []

        print(f"\nRunning {label_m} -> {label_s} ({N} iterations)...", flush=True)
        for _ in range(N):
            m_res, m_rtt, m_err, m_len = client.execute(m_sid, m_fc, m_addr, m_cnt)
            if m_res:
                ok_m += 1
                bytes_m = m_len + 6 # MBAP + body
            time.sleep(0.02) # 20ms delay

            s_res, s_rtt, s_err, s_len = client.execute(s_sid, s_fc, s_addr, s_cnt)
            if s_res:
                ok_s += 1
                rtts_s.append(s_rtt)
            time.sleep(0.02)

        pct_s = (ok_s / N) * 100
        verdict = "Flawless" if pct_s == 100 else ("Degraded" if pct_s >= 80 else "Severe Failure")
        row = f"| {label_m} | ~{bytes_m} B | {label_s} | 20ms | {N} | {ok_m}/{N} | {ok_s}/{N} | **{pct_s:5.1f}%** | {verdict} |"
        report_lines.append(row)
        print(f"-> MAGNA3: {ok_m}/{N} OK | SDM-GH: {ok_s}/{N} OK ({pct_s:.1f}%) | Verdict: {verdict}")

    client.close()

    with open(REPORT_PATH, "a") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\nVerification test complete and appended to {REPORT_PATH}")

if __name__ == "__main__":
    run_test()
