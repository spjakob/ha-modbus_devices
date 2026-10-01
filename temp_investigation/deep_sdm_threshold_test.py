import socket
import struct
import time
import select

GATEWAY_HOST = "192.168.1.5"
GATEWAY_PORT = 502

class RobustModbusClient:
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
            try:
                self.connect()
            except Exception as e:
                return False, (time.perf_counter() - t0)*1000, f"ConnErr: {e}", 0

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
                self.close() # Clean socket on timeout to avoid buffer poisoning
                return False, (time.perf_counter() - t0)*1000, "Timeout", 0

            try:
                mbap = self.read_exact(6, timeout=rem)
                resp_tid, pid, length = struct.unpack(">HHH", mbap)
                rem = deadline - time.perf_counter()
                if rem <= 0:
                    self.close()
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
                    self.close() # Reconnect on mismatch to re-sync
                    return False, rtt, f"UnitMismatch_{unit}", len(body)

                return True, rtt, "", len(body)
            except socket.timeout:
                self.close()
                return False, (time.perf_counter() - t0)*1000, "Timeout", 0
            except Exception as e:
                self.close()
                return False, (time.perf_counter() - t0)*1000, f"RecvErr: {e}", 0

def run_investigation():
    client = RobustModbusClient()
    client.connect()

    print("\n" + "="*80)
    print("EXPERIMENT 1: DELAY SWEEP ON 88-REGISTER ALTERNATING READS (GH <-> HB)")
    print("Testing if delays up to 2.0s allow large reads when switching meters")
    print("="*80)

    delays = [0.05, 0.10, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
    results_delay = []
    N = 8 # 8 alternating cycles = 16 queries per delay

    for d in delays:
        ok_gh = 0
        ok_hb = 0
        rtts = []
        for _ in range(N):
            r1, rtt1, _, _ = client.execute(102, 4, 0, 88)
            if r1: ok_gh += 1; rtts.append(rtt1)
            time.sleep(d)

            r2, rtt2, _, _ = client.execute(101, 4, 0, 88)
            if r2: ok_hb += 1; rtts.append(rtt2)
            time.sleep(d)

        total_succ = ok_gh + ok_hb
        pct = (total_succ / (2 * N)) * 100
        avg_rtt = f"{sum(rtts)/len(rtts):.1f}ms" if rtts else "N/A"
        results_delay.append((d, ok_gh, ok_hb, N, pct, avg_rtt))
        print(f"Delay: {d*1000:6.0f} ms | GH (102): {ok_gh}/{N} | HB (101): {ok_hb}/{N} | Total: {total_succ}/{2*N} ({pct:5.1f}%) | Avg RTT: {avg_rtt}")

    print("\n" + "="*80)
    print("EXPERIMENT 2: EXACT REGISTER COUNT THRESHOLD (Alternating GH <-> HB with 50ms delay)")
    print("Finding the exact byte/register boundary where alternating fails")
    print("="*80)

    counts = [10, 16, 20, 24, 30, 36, 42, 48, 56, 64, 72, 80, 88]
    results_count = []
    M = 8 # 8 alternating cycles = 16 queries per count

    for cnt in counts:
        ok_gh = 0
        ok_hb = 0
        rtts = []
        bytes_wire = 5 + (cnt * 2)

        for _ in range(M):
            r1, rtt1, _, _ = client.execute(102, 4, 0, cnt)
            if r1: ok_gh += 1; rtts.append(rtt1)
            time.sleep(0.05) # 50ms standard delay

            r2, rtt2, _, _ = client.execute(101, 4, 0, cnt)
            if r2: ok_hb += 1; rtts.append(rtt2)
            time.sleep(0.05)

        total_succ = ok_gh + ok_hb
        pct = (total_succ / (2 * M)) * 100
        avg_rtt = f"{sum(rtts)/len(rtts):.1f}ms" if rtts else "N/A"
        results_count.append((cnt, bytes_wire, ok_gh, ok_hb, M, pct, avg_rtt))
        status = "🟢 100% Stable" if pct == 100 else ("🟡 Minor drop" if pct >= 80 else "🔴 Collapsed")
        print(f"Regs: {cnt:2d} ({bytes_wire:3d} B) | GH: {ok_gh}/{M} | HB: {ok_hb}/{M} | Total: {pct:5.1f}% | {status}")

    client.close()

    # Save raw results to a dedicated file
    out_file = "/tmp/threshold_results.txt"
    with open(out_file, "w") as f:
        f.write("=== DELAY SWEEP (88 REGS) ===\n")
        for d, gh, hb, n, pct, rtt in results_delay:
            f.write(f"{d*1000:.0f}ms | {gh}/{n} | {hb}/{n} | {pct:.1f}% | {rtt}\n")
        f.write("\n=== REGISTER COUNT SWEEP (50ms DELAY) ===\n")
        for cnt, b, gh, hb, m, pct, rtt in results_count:
            f.write(f"{cnt} regs ({b}B) | {gh}/{m} | {hb}/{m} | {pct:.1f}% | {rtt}\n")

    print(f"\nRaw results written to {out_file}")

if __name__ == "__main__":
    run_investigation()
