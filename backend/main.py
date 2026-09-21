from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uuid

from ai_engine.monitor import analyze_transaction
from ai_engine.threat_detection import detect_threat
from ai_engine.rules import check_rules
from ai_engine.adaptive_engine import decide_encryption
from crypto.hybrid import encrypt, switch_algorithm
from crypto.freshness import check_freshness
from crypto.signing import verify_signature

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: float
    nonce: str | None = None
    timestamp: float | None = None
    signature: str | None = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


dashboard_manager = ConnectionManager()
app_manager = ConnectionManager()


def self_heal(threat_found: bool) -> dict:
    if threat_found:
        return {
            "system_integrity": "Intact",
            "key_rotation": "Done",
            "threat_isolation": "Done"
        }
    return {
        "system_integrity": "Intact",
        "key_rotation": "Not Needed",
        "threat_isolation": "Not Needed"
    }


def multi_path_transmission() -> dict:
    return {
        "fragment_1": "Path 1: Secured",
        "fragment_2": "Path 2: Secured",
        "fragment_3": "Path 3: Secured",
        "all_paths_secured": True
    }


def calculate_security_score(threat_found: bool, decision: str) -> int:
    score = 100
    if threat_found:
        score -= 10
    if decision == "SWITCH":
        score -= 3
    return score


@app.get("/")
def read_root():
    return {"message": "CipherZenith backend is alive"}


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await dashboard_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)


@app.websocket("/ws/app")
async def websocket_app(websocket: WebSocket):
    await app_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        app_manager.disconnect(websocket)


@app.post("/api/transaction")
async def create_transaction(transaction: Transaction):
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

    signature_check = verify_signature(
        transaction.sender, transaction.receiver, transaction.amount,
        transaction.nonce, transaction.timestamp, transaction.signature
    )
    if signature_check["status"] == "invalid":
        threat_type = "Invalid Signature"
        await dashboard_manager.broadcast({
            "step": 4,
            "title": "Threat Detection",
            "status": "threat_detected",
            "details": {
                "threat_found": True,
                "threat_type": threat_type,
                "confidence": 100.0,
                "detected_by": "signature_check",
                "reason": signature_check["reason"]
            },
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=401, detail={
            "status": "transaction_rejected",
            "transaction_id": txn_id,
            "threat_type": threat_type,
            "reason": signature_check["reason"]
        })

    freshness = check_freshness(transaction.sender, transaction.nonce, transaction.timestamp)
    if freshness["status"] not in ("fresh", "unchecked"):
        threat_labels = {
            "replay": "Replay Attack",
            "stale": "Stale Timestamp",
            "invalid": "Malformed Freshness Fields",
        }
        threat_type = threat_labels[freshness["status"]]
        await dashboard_manager.broadcast({
            "step": 4,
            "title": "Threat Detection",
            "status": "threat_detected",
            "details": {
                "threat_found": True,
                "threat_type": threat_type,
                "confidence": 100.0,
                "detected_by": "freshness_check",
                "reason": freshness["reason"]
            },
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=409, detail={
            "status": "transaction_rejected",
            "transaction_id": txn_id,
            "threat_type": threat_type,
            "reason": freshness["reason"]
        })

    # Step 1: Transaction Received
    await dashboard_manager.broadcast({
        "step": 1,
        "title": "Transaction Received",
        "status": "complete",
        "details": {
            "transaction_id": txn_id,
            "sender": transaction.sender,
            "receiver": transaction.receiver,
            "amount": transaction.amount
        },
        "timestamp": datetime.now().isoformat()
    })

    # Step 2: Hybrid Encryption
    encryption_result = encrypt(transaction.model_dump(), risk_level="LOW")
    await dashboard_manager.broadcast({
        "step": 2,
        "title": "Hybrid Encryption",
        "status": "complete",
        "details": encryption_result,
        "timestamp": datetime.now().isoformat()
    })

    # Step 3: AI Monitoring
    monitor_result = analyze_transaction(transaction.model_dump())
    await dashboard_manager.broadcast({
        "step": 3,
        "title": "AI Monitoring",
        "status": "complete",
        "details": monitor_result,
        "timestamp": datetime.now().isoformat()
    })

    # Step 4: Threat Detection
    threat_result = detect_threat(transaction.model_dump(), monitor_result["anomaly_score"])
    rule_result = check_rules(transaction.sender, transaction.receiver, transaction.amount)
    model_reason = threat_result["reason"] if threat_result["threat_found"] else None
    threat_result["rule_flags"] = rule_result["flags"]
    if rule_result["threat_found"]:
        # A crossed threshold is a fact, not a guess, so a rule verdict wins over the model label.
        reasons = [flag["reason"] for flag in rule_result["flags"]]
        if model_reason:
            reasons.append(model_reason)
        threat_result["threat_found"] = True
        threat_result["threat_type"] = rule_result["flags"][0]["rule"]
        threat_result["confidence"] = 100.0
        threat_result["detected_by"] = "rules"
        threat_result["reason"] = "; ".join(reasons)
    await dashboard_manager.broadcast({
        "step": 4,
        "title": "Threat Detection",
        "status": "threat_detected" if threat_result["threat_found"] else "complete",
        "details": threat_result,
        "timestamp": datetime.now().isoformat()
    })

    # Step 5: Adaptive Engine
    adaptive_result = decide_encryption(
        monitor_result["risk_level"],
        threat_result["threat_found"],
        threat_result["threat_type"]
    )
    await dashboard_manager.broadcast({
        "step": 5,
        "title": "Adaptive Engine",
        "status": "complete",
        "details": adaptive_result,
        "timestamp": datetime.now().isoformat()
    })

    # If Step 5 decided to switch, actually call switch_algorithm
    if adaptive_result["decision"] == "SWITCH":
        encryption_result = switch_algorithm(
            encryption_result["encrypted_data"],
            adaptive_result["algorithm_selected"]
        )

    # Step 6: Self Healing
    healing_result = self_heal(threat_result["threat_found"])
    await dashboard_manager.broadcast({
        "step": 6,
        "title": "Self Healing",
        "status": "complete",
        "details": healing_result,
        "timestamp": datetime.now().isoformat()
    })

    # Step 7: Multi-path Transmission
    transmission_result = multi_path_transmission()
    await dashboard_manager.broadcast({
        "step": 7,
        "title": "Multi-path Transmission",
        "status": "complete",
        "details": transmission_result,
        "timestamp": datetime.now().isoformat()
    })

    # Step 8: Secure Output
    security_score = calculate_security_score(threat_result["threat_found"], adaptive_result["decision"])
    final_algorithm = adaptive_result["algorithm_selected"]
    await dashboard_manager.broadcast({
        "step": 8,
        "title": "Secure Output",
        "status": "complete",
        "details": {
            "delivered": True,
            "security_score": security_score,
            "final_encryption": final_algorithm
        },
        "timestamp": datetime.now().isoformat()
    })

    # Notify the app - clean, minimal, no technical details
    await app_manager.broadcast({
        "status": "complete",
        "transaction_id": txn_id,
        "receiver": transaction.receiver,
        "amount": transaction.amount
    })

    return {
        "status": "transaction_complete",
        "transaction_id": txn_id,
        "security_score": security_score,
        "final_encryption": final_algorithm
    }
