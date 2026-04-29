import boto3
import json
import os
import pandas as pd
from io import BytesIO
from twilio.rest import Client
from twilio.request_validator import RequestValidator

# ── Clients ───────────────────────────────────────────────────────────────────
bedrock   = boto3.client("bedrock-runtime", region_name="us-east-1")
dynamodb  = boto3.resource("dynamodb")
s3        = boto3.client("s3")

HISTORY_TABLE = os.environ["HISTORY_TABLE"]   # DynamoDB table name
TWILIO_SID    = os.environ["TWILIO_SID"]
TWILIO_TOKEN  = os.environ["TWILIO_TOKEN"]
TWILIO_NUMBER = os.environ["TWILIO_WHATSAPP_NUMBER"]  # e.g. whatsapp:+14155238886
MODEL_ID      = "us.anthropic.claude-sonnet-4-20250514-v1:0"

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)
table         = dynamodb.Table(HISTORY_TABLE)

# ── System prompt — this is your CA's personality ────────────────────────────
SYSTEM_PROMPT = """You are FinBot, a expert Chartered Accountant assistant specializing in:
- Tally ERP 9 and TallyPrime troubleshooting
- Bank reconciliation (BRS)
- GST filing, TDS, and Indian taxation
- Accounts payable/receivable
- Financial KPIs and MIS reports

Rules:
- Always respond in simple, practical language a CA can act on immediately
- For reconciliation queries, show the mismatch clearly in a table format with reasons
- Cite relevant Indian accounting standards or GST rules when applicable
- If a file is uploaded, compare data irresetive of the data format analyze it and provide specific observations
- Keep replies concise — this is WhatsApp, not email
- If unsure, say so clearly rather than guessing on financial matters"""


# ── Chat history (DynamoDB) ───────────────────────────────────────────────────
def get_history(phone: str) -> list:
    try:
        resp = table.get_item(Key={"phone": phone})
        return resp.get("Item", {}).get("messages", [])
    except:
        return []

def save_history(phone: str, messages: list):
    # Keep last 10 exchanges to stay within token limits
    trimmed = messages[-20:]
    table.put_item(Item={"phone": phone, "messages": trimmed})


# ── File handler — Excel/CSV reconciliation ──────────────────────────────────
def analyze_file(media_url: str, content_type: str) -> str:
    """Download file from Twilio, parse with pandas, return summary for Claude."""
    import requests
    auth = (TWILIO_SID, TWILIO_TOKEN)
    resp = requests.get(media_url, auth=auth)
    data = BytesIO(resp.content)

    try:
        if "csv" in content_type:
            df = pd.read_csv(data)
        else:
            df = pd.read_excel(data)

        summary = f"""File uploaded — {len(df)} rows, {len(df.columns)} columns.
Columns: {', '.join(df.columns.tolist())}
First 5 rows:
{df.head().to_string()}

Numeric summary:
{df.describe().to_string()}"""
        return summary
    except Exception as e:
        return f"Could not parse file: {e}"


# ── RAG retrieval (OpenSearch) ────────────────────────────────────────────────
def retrieve_context(query: str) -> str:
    """
    Stub — replace with your OpenSearch call.
    For quick start: skip this and rely on Claude's built-in Tally knowledge.
    Add PDFs later by uploading to S3 + indexing into OpenSearch Serverless.
    """
    return ""  # return relevant chunks when OpenSearch is ready


# ── Core: call Claude ─────────────────────────────────────────────────────────
def ask_claude(phone: str, user_message: str, file_context: str = "") -> str:
    history = get_history(phone)

    # Build the user content — text + optional file analysis
    content = user_message
    if file_context:
        content += f"\n\n[File data]\n{file_context}"

    # Add RAG context if available
    rag_context = retrieve_context(user_message)
    if rag_context:
        content += f"\n\n[Relevant knowledge base]\n{rag_context}"

    history.append({"role": "user", "content": content})

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": history
        }),
        contentType="application/json",
        accept="application/json"
    )

    result  = json.loads(response["body"].read())
    answer  = result["content"][0]["text"]
    usage   = result.get("usage", {})

    history.append({"role": "assistant", "content": answer})
    save_history(phone, history)

    print(f"Tokens used — in: {usage.get('input_tokens')} out: {usage.get('output_tokens')}")
    return answer


# ── WhatsApp reply ────────────────────────────────────────────────────────────
def send_whatsapp(to: str, message: str):
    # WhatsApp has 1600 char limit — split if needed
    chunks = [message[i:i+1500] for i in range(0, len(message), 1500)]
    for chunk in chunks:
        twilio_client.messages.create(
            from_=TWILIO_NUMBER,
            to=f"whatsapp:{to}",
            body=chunk
        )


# ── Lambda entrypoint ─────────────────────────────────────────────────────────
def lambda_handler(event, context):
    # Parse Twilio's form-encoded webhook
    body    = dict(item.split("=") for item in event["body"].split("&"))
    phone   = body.get("From", "").replace("whatsapp%3A", "").replace("%2B", "+")
    text    = body.get("Body", "").replace("+", " ")
    num_media = int(body.get("NumMedia", 0))

    print(f"Message from {phone}: {text[:80]}")

    file_context = ""
    if num_media > 0:
        media_url     = body.get("MediaUrl0", "")
        content_type  = body.get("MediaContentType0", "")
        file_context  = analyze_file(media_url, content_type)

    # Special commands
    if text.strip().lower() in ["/reset", "reset", "clear"]:
        save_history(phone, [])
        send_whatsapp(phone, "Chat history cleared. Fresh start!")
        return {"statusCode": 200}

    answer = ask_claude(phone, text, file_context)
    send_whatsapp(phone, answer)

    return {"statusCode": 200, "body": "OK"}