import boto3
import json

def main():
    print("🚀 Working Bedrock Integration")
    print("=" * 50)

    bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

    # ✅ Fix 3: Claude Sonnet 4 requires a cross-region inference profile
    # ✅ Fix 1: NVIDIA Nemotron uses messages format (OpenAI-compatible)
    # ✅ Fix 2: Titan lite v2 replaced with Nova — Titan is deprecated/unavailable
    test_models = [
        {
            "id": "us.nvidia.nemotron-nano-12b-v2:0",   # needs region prefix + version suffix
            "format": "messages"
        },
        {
            "id": "us.amazon.nova-lite-v1:0",            # Titan replaced by Nova
            "format": "nova"
        },
        {
            "id": "us.anthropic.claude-sonnet-4-20250514-v1:0",  # cross-region profile
            "format": "claude"
        },
    ]

    prompt = "Why did NASA launch the Artemis mission? What does NASA want to learn about space?"

    for model in test_models:
        model_id = model["id"]
        fmt = model["format"]
        print(f"\n🔄 Testing {model_id}...")

        try:
            # --- Build request body per model family ---
            if fmt == "claude":
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                }
            elif fmt == "nova":
                body = {
                    "messages": [{"role": "user", "content": [{"text": prompt}]}],
                    "inferenceConfig": {"max_new_tokens": 300}
                }
            elif fmt == "messages":
                # NVIDIA Nemotron: OpenAI-compatible messages format
                body = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400,
                    "temperature": 0.7
                }

            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )

            result = json.loads(response["body"].read())

            # --- Parse response per model family ---
            if fmt == "claude":
                answer = result["content"][0]["text"]
            elif fmt == "nova":
                answer = result["output"]["message"]["content"][0]["text"]
            elif fmt == "messages":
                answer = result["choices"][0]["message"]["content"]

            print(f"✅ {model_id}")
            print(f"   {answer[:400]}")

        except Exception as e:
            print(f"❌ {model_id}: {e}")

if __name__ == "__main__":
    main()