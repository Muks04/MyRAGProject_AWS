import boto3
import json

prompt_Data = """
Why NASA launched the space mission recently with Artemis. What's NASA wants to know abut space?
"""

# Updated model parameters that actually work
MODEL_PARAMETERS = {
    # Try these models - they work most places
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "maxTokens": 150,
        "temperature": 0.7,
        "topK": 250,
        "topP": 0.95
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "maxTokens": 100,
        "temperature": 0.8
    },
    "amazon.titan-text-lite-v1:0": {
        "max_new_tokens": 150,
        "top_k": 250,
        "top_p": 0.95,
        "temperature": 0.7
    },
    "amazon.titan-text-express-v1": {
        "max_new_tokens": 200,
        "top_k": 50,
        "top_p": 0.9,
        "temperature": 0.7
    },
    "meta.llama3-8b-instruct-v1:0": {
        "max_new_tokens": 150,
        "temperature": 0.7
    }
}

def call_bedrock_model(prompt, model_id):
    """Call Bedrock with model-specific parameters"""
    
    try:
        # Get model-specific parameters
        params = MODEL_PARAMETERS.get(model_id, {"prompt": prompt})
        
        # Always include the prompt
        params["prompt"] = prompt
        
        # Prepare request
        body = json.dumps(params)
        
        # Make API call
        bedrock = boto3.client("bedrock-runtime")
        response = bedrock.invoke_model(modelId=model_id, body=body)
        
        # Parse response
        response_body = response['body'].read()
        response_str = response_body.decode('utf-8')
        response_data = json.loads(response_str)
        
        if 'content' in response_data and response_data['content']:
            return response_data['content'][0]['text']
        else:
            return "No response content found"
            
    except Exception as e:
        return f"Error: {e}"

def main():
    """Test with the most likely working model"""
    
    # Try the most popular model first
    test_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    print("Testing with Claude 3 Sonnet...")
    response = call_bedrock_model(prompt_Data, test_model)
    
    if response and not response.startswith("Error:"):
        print("✅ SUCCESS!")
        print("Response:", response)
    else:
        print("❌ Failed with that model. Trying alternatives...")
        
        # Try other models
        for model in ["amazon.titan-text-lite-v1:0", "meta.llama3-8b-instruct-v1:0"]:
            print(f"\nTrying {model}...")
            response = call_bedrock_model(prompt_Data, model)
            if response and not response.startswith("Error:"):
                print("✅ SUCCESS!")
                print("Response:", response)
                break
        else:
            print("❌ All models failed. Check your AWS setup.")

if __name__ == "__main__":
    main()
        