import boto3
import json
import time
import uuid
import logging
import structlog
from aws_xray_sdk.core import xray_recorder, patch_all
from botocore.config import Config
from botocore.exceptions import ClientError

# --- Patch all boto3 clients for X-Ray tracing ---
patch_all()

# --- Structured logging (outputs JSON to CloudWatch) ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.BoundLogger,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()

# --- Boto3 clients with retry config ---
RETRY_CONFIG = Config(retries={"max_attempts": 3, "mode": "adaptive"})
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1", config=RETRY_CONFIG)
cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

EMBED_MODEL  = "us.amazon.nova-lite-v1:0"
GENERATE_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0"
NAMESPACE = "RAGService"


# ── Observability helpers ─────────────────────────────────────────────────────

def emit_metric(name: str, value: float, unit: str = "Count", dimensions: dict = {}):
    """Push a single metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[{
                "MetricName": name,
                "Value": value,
                "Unit": unit,
                "Dimensions": [{"Name": k, "Value": v} for k, v in dimensions.items()]
            }]
        )
    except Exception as e:
        log.warning("metric_emit_failed", metric=name, error=str(e))


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Rough cost estimate in USD — update prices as AWS changes them."""
    pricing = {
        "us.anthropic.claude-sonnet-4-20250514-v1:0": (0.003, 0.015),  # per 1K tokens
    }
    in_price, out_price = pricing.get(model, (0.001, 0.005))
    return round((input_tokens * in_price + output_tokens * out_price) / 1000, 6)


# ── Core RAG steps ────────────────────────────────────────────────────────────

@xray_recorder.capture("embed_query")
def embed_query(query: str, request_id: str) -> list[float]:
    """Embed the user query using Bedrock Nova."""
    t0 = time.monotonic()
    try:
        response = bedrock_runtime.invoke_model(
            modelId=EMBED_MODEL,
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": query}]}],
                "inferenceConfig": {"max_new_tokens": 8}
            }),
            contentType="application/json",
            accept="application/json"
        )
        # NOTE: swap this for a real embedding model (Titan Embed, Cohere) in prod
        # Nova is used here to keep the example self-contained
        latency = (time.monotonic() - t0) * 1000
        log.info("embed_complete", request_id=request_id, latency_ms=round(latency, 2))
        emit_metric("EmbedLatency", latency, "Milliseconds")
        return []  # replace with actual embedding vector
    except ClientError as e:
        log.error("embed_failed", request_id=request_id, error=str(e))
        emit_metric("EmbedErrors", 1)
        raise


@xray_recorder.capture("retrieve_chunks")
def retrieve_chunks(embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Query your vector store. Swap the stub below for your real client:
      - OpenSearch:  opensearch-py
      - pgvector:    psycopg2 + SELECT ... ORDER BY embedding <-> %s LIMIT %s
      - Pinecone:    pinecone.Index.query(vector=embedding, top_k=top_k)
    """
    # STUB — replace with real vector store call
    return [
        {"text": "Artemis is NASA's lunar exploration program.", "score": 0.92, "source": "nasa_artemis.pdf"},
        {"text": "Artemis I launched in November 2022 as an uncrewed test.", "score": 0.88, "source": "nasa_artemis.pdf"},
    ]


@xray_recorder.capture("generate_answer")
def generate_answer(query: str, chunks: list[dict], request_id: str) -> dict:
    """Call Bedrock with the retrieved context and return the full result."""
    context = "\n\n".join(
        f"[Source: {c['source']} | score: {c['score']}]\n{c['text']}"
        for c in chunks
    )
    prompt = f"""You are a helpful assistant. Answer using ONLY the context below.
If the context doesn't contain enough information, say so clearly.

Context:
{context}

Question: {query}

Answer:"""

    t0 = time.monotonic()
    try:
        response = bedrock_runtime.invoke_model(
            modelId=GENERATE_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}]
            }),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read())
        latency = (time.monotonic() - t0) * 1000

        input_tokens  = result["usage"]["input_tokens"]
        output_tokens = result["usage"]["output_tokens"]
        cost = estimate_cost(input_tokens, output_tokens, GENERATE_MODEL)

        log.info("generate_complete",
            request_id=request_id,
            latency_ms=round(latency, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost
        )
        emit_metric("GenerateLatency", latency, "Milliseconds")
        emit_metric("TokensUsed", input_tokens + output_tokens)
        emit_metric("EstimatedCostUSD", cost, "None")

        return {
            "answer": result["content"][0]["text"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "latency_ms": round(latency, 2),
        }
    except ClientError as e:
        log.error("generate_failed", request_id=request_id, error=str(e))
        emit_metric("GenerateErrors", 1)
        raise


# ── Public entrypoint ─────────────────────────────────────────────────────────

@xray_recorder.capture("rag_query")
def rag_query(query: str) -> dict:
    request_id = str(uuid.uuid4())
    log.info("request_start", request_id=request_id, query=query[:120])
    t_total = time.monotonic()

    try:
        embedding = embed_query(query, request_id)
        chunks    = retrieve_chunks(embedding)
        result    = generate_answer(query, chunks, request_id)

        total_ms = round((time.monotonic() - t_total) * 1000, 2)
        emit_metric("TotalLatency", total_ms, "Milliseconds")

        return {
            "request_id": request_id,
            "answer": result["answer"],
            "sources": [{"source": c["source"], "score": c["score"]} for c in chunks],
            "usage": {
                "input_tokens":  result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "cost_usd":      result["cost_usd"],
            },
            "latency_ms": total_ms,
        }
    except Exception as e:
        log.error("request_failed", request_id=request_id, error=str(e))
        emit_metric("RequestErrors", 1)
        raise


if __name__ == "__main__":
    out = rag_query("Why did NASA launch the Artemis mission?")
    print(json.dumps(out, indent=2))