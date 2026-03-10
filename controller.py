from flask import Flask, request, jsonify
import sqlite3, datetime

app = Flask(__name__)
DB = "sdwan.db"

def init_db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id TEXT,
            wan TEXT,
            latency_ms REAL,
            packet_loss_pct REAL,
            timestamp TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id TEXT,
            active_wan TEXT,
            reason TEXT,
            timestamp TEXT
        )
    """)
    con.commit()
    con.close()

def decide(wan1, wan2):
    def score(m):
        return m["latency_ms"] + (m["packet_loss_pct"] * 10)
    if score(wan1) <= score(wan2) * 1.2:
        return "WAN1", f"WAN1 score={score(wan1):.1f}"
    return "WAN2", f"WAN2 score={score(wan2):.1f} better"

@app.route("/api/metrics", methods=["POST"])
def receive_metrics():
    data = request.json
    branch = data["branch_id"]
    wan1, wan2 = data["wan1"], data["wan2"]
    ts = datetime.datetime.utcnow().isoformat()
    con = sqlite3.connect(DB)
    for label, m in [("WAN1", wan1), ("WAN2", wan2)]:
        con.execute(
            "INSERT INTO metrics VALUES (NULL,?,?,?,?,?)",
            (branch, label, m["latency_ms"], m["packet_loss_pct"], ts)
        )
    active, reason = decide(wan1, wan2)
    con.execute(
        "INSERT INTO decisions VALUES (NULL,?,?,?,?)",
        (branch, active, reason, ts)
    )
    con.commit()
    con.close()
    return jsonify({"active_wan": active, "reason": reason})

@app.route("/api/decisions/<branch_id>", methods=["GET"])
def get_decisions(branch_id):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT active_wan, reason, timestamp FROM decisions WHERE branch_id=? ORDER BY id DESC LIMIT 20",
        (branch_id,)
    ).fetchall()
    con.close()
    return jsonify([{"active_wan": r[0], "reason": r[1], "ts": r[2]} for r in rows])

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
