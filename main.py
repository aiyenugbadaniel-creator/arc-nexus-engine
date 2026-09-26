import logging
import os

import requests
from fastapi import FastAPI, HTTPException, Request, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arc_nexus_backend")

app = FastAPI(title="ARC NEXUS Engine")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv(
    "WHATSAPP_VERIFY_TOKEN", "arc_nexus_webhook_verify_secret_2026"
)


@app.get("/")
def read_root():
    return {"status": "online", "system": "ARC NEXUS Engine"}


@app.get("/webhooks/whatsapp")
def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge", "")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@app.post("/webhooks/whatsapp")
async def receive_whatsapp_message(request: Request):
    data = await request.json()
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                messages = change.get("value", {}).get("messages", [])
                if messages:
                    message = messages[0]
                    from_number = message.get("from")
                    text_body = message.get("text", {}).get("body", "")
                    response_text = generate_arc_response(text_body)
                    send_whatsapp_reply(from_number, response_text)
    except Exception as error:
        logger.error("Error: %s", error)

    return Response(content="EVENT_RECEIVED", status_code=200)


def generate_arc_response(user_text: str) -> str:
    if user_text.lower().startswith("/lga"):
        lga_name = user_text.replace("/lga", "", 1).strip() or "Target LGA"
        return (
            f"🏛️ *ARC NEXUS Audit Matrix: {lga_name}*\n\n"
            "• *Governance Status:* Decentralized Civic Protocol Active [FACT]\n"
            "• *Fiscal Target:* OSI Threshold = 1.35 (Approved) [EVIDENCE]\n"
            "• *Reform Mandate:* Direct LGA revenue autonomy under constitutional reforms [LAW]\n\n"
            "Type `/aldi` for sectoral breakdown or `/budget` for capital expenditure analysis."
        )
    return (
        f"🤖 *ARC NEXUS Active*\n\nReceived: \"{user_text}\" [FACT]\n\n"
        "Arc Nigeria advocates for local government transformation and fiscal autonomy [ARC POSITION]."
    )


def send_whatsapp_reply(recipient_phone: str, message_text: str) -> None:
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": message_text},
    }
    requests.post(url, headers=headers, json=payload)

