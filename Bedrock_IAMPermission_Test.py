# iam_permissions_test.py
import boto3
import json

def check_bedrock_permissions():
    """Check if you have the necessary IAM permissions for Bedrock"""
    
    print("🔐 Checking Bedrock IAM permissions...")
    
    try:
        # List available services (to confirm AWS is working)
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account ID: {identity.get('Account', 'Unknown')}")
        print(f"✅ User/Role: {identity.get('Arn', 'Unknown')}")
        
        # Try Bedrock actions
        bedrock = boto3.client('bedrock-runtime')
        
        print("\n🚀 Testing Bedrock permissions...")
        
        # Test 1: List models
        try:
            response = bedrock.list_foundation_models()
            models = response['modelSummaries']
            print(f"✅ bedrock:ListFoundationModels - ALLOWED ({len(models)} models found)")
        except Exception as e:
            print(f"❌ bedrock:ListFoundationModels - DENIED: {e}")
        
        # Test 2: Invoke model (using a simple model)
        try:
            body = json.dumps({"prompt": "Test"})
            response = bedrock.invoke_model(
                modelId="amazon.titan-text-lite-v1:0",
                body=body
            )
            print("✅ bedrock:InvokeModel - ALLOWED")
        except Exception as e:
            print(f"❌ bedrock:InvokeModel - DENIED: {e}")
        
        # Test 3: List inference profiles
        try:
            response = bedrock.list_inference_profiles()
            print("✅ bedrock:ListInferenceProfiles - ALLOWED")
        except Exception as e:
            print(f"❌ bedrock:ListInferenceProfiles - DENIED: {e}")
            
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")

# Run this test
if __name__ == "__main__":
    check_bedrock_permissions()