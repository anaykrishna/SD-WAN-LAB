import subprocess, requests, time

CONTROLLER = "http://<host-ip>:5000"
BRANCH_ID  = "branch-A"   # change to branch-B on Client-B
WAN1_GW    = "10.1.1.1"   # pfSense-A WAN1 — change to 10.1.1.2 on Client-B
WAN2_GW    = "10.2.2.1"   # pfSense-A WAN2 — change to 10.2.2.2 on Client-B

def measure(gateway):
    result = subprocess.run(
        ["ping", "-c", "10", "-W", "1", gateway],
        capture_output=True, text=True
    )
    latency, loss = 999.0, 100.0
    for line in result.stdout.split("\n"):
        if "avg" in line:
            latency = float(line.split("/")[4])
        if "packet loss" in line:
            loss = float(line.split("%")[0].split()[-1])
    return {"latency_ms": latency, "packet_loss_pct": loss}

def report():
    while True:
        wan1 = measure(WAN1_GW)
        wan2 = measure(WAN2_GW)
        payload = {
            "branch_id": BRANCH_ID,
            "wan1": wan1,
            "wan2": wan2
        }
        try:
            r = requests.post(f"{CONTROLLER}/api/metrics", json=payload)
            print("Sent:", payload, "| Decision:", r.json())
        except Exception as e:
            print("Controller unreachable:", e)
        time.sleep(10)

if __name__ == "__main__":
    report()
