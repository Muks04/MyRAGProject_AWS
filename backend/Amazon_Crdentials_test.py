# # credentials_test.py
# import boto3
# import os
# from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# def test_aws_credentials():
#     """Test if AWS credentials are properly configured"""
    
#     print("🔍 Testing AWS credentials...")
    
#     # Check if environment variables are set
#     print(f"AWS_ACCESS_KEY_ID: {'SET' if os.getenv('AWS_ACCESS_KEY_ID') else 'NOT SET'}")
#     print(f"AWS_SECRET_ACCESS_KEY: {'SET' if os.getenv('AWS_SECRET_ACCESS_KEY') else 'NOT SET'}")
#     print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION', 'Not set')}")
    
#     # Test credentials by creating a basic S3 client
#     try:
#         s3 = boto3.client('s3')
#         print("✅ AWS credentials are valid and can access S3")
        
#         # Try to list buckets (even if none exist)
#         buckets = s3.list_buckets()
#         print(f"✅ Can list {len(buckets['Buckets'])} S3 buckets")
        
#         return True
        
#     except NoCredentialsError:
#         print("❌ No AWS credentials found")
#         print("💡 Set your credentials:")
#         print("   export AWS_ACCESS_KEY_ID=your_key")
#         print("   export AWS_SECRET_ACCESS_KEY=your_secret")
#         print("   export AWS_DEFAULT_REGION=us-east-1")
#         return False
        
#     except PartialCredentialsError:
#         print("❌ Incomplete AWS credentials")
#         print("💡 Make sure both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set")
#         return False
        
#     except Exception as e:
#         print(f"❌ AWS credentials error: {e}")
#         return False

# # Run this first
# if __name__ == "__main__":
#     test_aws_credentials()

# discover_bedrock_api.py
import boto3
import inspect

def discover_bedrock_methods():
    """Discover what methods are actually available"""
    
    print("🔍 Discovering Bedrock API methods...")
    
    # Try different service names
    service_names = ["bedrock", "bedrock-runtime", "bedrock-runtime"]
    
    for service_name in service_names:
        print(f"\n📍 Trying service: {service_name}")
        print("-" * 40)
        
        try:
            # Create client
            if service_name == "bedrock":
                client = boto3.client("bedrock")
            else:
                client = boto3.client(service_name="bedrock-runtime")
            
            print("✅ Client created successfully")
            
            # Get all available methods
            methods = [method for method in dir(client) if not method.startswith('_')]
            
            print(f"📋 Available methods ({len(methods)}):")
            for method in sorted(methods):
                if 'model' in method.lower() or 'inference' in method.lower():
                    print(f"  - {method}")
                    
            return client, service_name
            
        except Exception as e:
            print(f"❌ Failed with {service_name}: {e}")
            continue
    
    return None, None

def test_basic_operations(client, service_name):
    """Test basic operations to see what works"""
    
    print(f"\n🧪 Testing operations with {service_name}...")
    
    # Try common operations
    operations_to_test = [
        ("list_foundation_models", lambda: client.list_foundation_models()),
        ("invoke_model", lambda: client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps({"prompt": "test"})
        )),
        ("create_inference_profile", lambda: client.create_inference_profile(
            inferenceProfileName="test-profile",
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0"
        )),
    ]
    
    for op_name, op_func in operations_to_test:
        try:
            print(f"\n🔄 Testing {op_name}...")
            result = op_func()
            print(f"✅ {op_name} works!")
            return True
        except Exception as e:
            print(f"❌ {op_name} failed: {e}")
            continue
    
    return False

# Run discovery
if __name__ == "__main__":
    client, service_name = discover_bedrock_methods()
    
    if client:
        test_basic_operations(client, service_name)
    else:
        print("❌ Could not create Bedrock client")
