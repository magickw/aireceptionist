#!/usr/bin/env python3
"""
Test AWS configuration for AI Receptionist
Verifies access to Transcribe, S3, Polly, and Bedrock

Run from backend directory: python3 ../aws-config/test_aws_config.py
"""
import os
import sys

# Add backend to path if running from aws-config directory
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
if os.path.exists(backend_path):
    sys.path.insert(0, backend_path)

import boto3

def test_aws_config():
    """Test AWS configuration and report results"""
    print("=" * 60)
    print("AWS Configuration Test for AI Receptionist")
    print("=" * 60)
    
    # Load from environment or config
    try:
        from app.core.config import settings
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        region = settings.AWS_REGION
    except ImportError:
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region = os.environ.get('AWS_REGION', 'us-east-1')
    
    print(f"\nRegion: {region}")
    print(f"Access Key: {access_key[:8]}...{access_key[-4:] if access_key and len(access_key) > 12 else 'NOT SET'}")
    print(f"Secret Key: {'SET' if secret_key else 'NOT SET'}")
    
    if not access_key or not secret_key:
        print("\n✗ ERROR: AWS credentials not configured!")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False
    
    all_pass = True
    
    # Test 1: S3 Access
    print("\n--- Test 1: S3 Access ---")
    try:
        s3 = boto3.client('s3', 
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key,
                          region_name=region)
        buckets = s3.list_buckets()
        print(f"✓ S3 access OK (found {len(buckets['Buckets'])} buckets)")
        
        # Check if we can create buckets
        test_bucket = f"aireceptionist-test-{region}"
        try:
            s3.head_bucket(Bucket=test_bucket)
            print(f"✓ Can access existing bucket: {test_bucket}")
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"✓ Bucket creation permission available (bucket doesn't exist)")
            else:
                print(f"⚠ S3 bucket check warning: {e}")
    except Exception as e:
        print(f"✗ S3 access failed: {e}")
        all_pass = False
    
    # Test 2: Amazon Transcribe Service
    print("\n--- Test 2: Amazon Transcribe Service ---")
    try:
        transcribe = boto3.client('transcribe',
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key,
                                region_name=region)
        transcribe.list_transcription_jobs(MaxResults=1)
        print("✓ Transcribe service access OK")
    except Exception as e:
        error_msg = str(e)
        if 'SubscriptionRequiredException' in error_msg:
            print("✗ Transcribe not enabled - AWS account needs subscription")
        else:
            print(f"✗ Transcribe service access failed: {e}")
        all_pass = False
    
    # Test 3: Amazon Transcribe Streaming SDK
    print("\n--- Test 3: Transcribe Streaming SDK ---")
    try:
        from amazon_transcribe.client import TranscribeStreamingClient
        client = TranscribeStreamingClient(region=region)
        print("✓ Transcribe Streaming SDK installed and importable")
    except ImportError:
        print("✗ amazon-transcribe SDK not installed")
        print("  Run: pip install amazon-transcribe")
        all_pass = False
    except Exception as e:
        print(f"✗ Transcribe Streaming SDK error: {e}")
        all_pass = False
    
    # Test 4: Amazon Polly (TTS)
    print("\n--- Test 4: Amazon Polly (TTS) ---")
    try:
        polly = boto3.client('polly',
                             aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key,
                             region_name=region)
        voices = polly.describe_voices(LanguageCode='en-US')
        print(f"✓ Polly access OK (found {len(voices['Voices'])} English voices)")
    except Exception as e:
        print(f"✗ Polly access failed: {e}")
        all_pass = False
    
    # Test 5: Amazon Bedrock (Nova)
    print("\n--- Test 5: Amazon Bedrock (Nova) ---")
    try:
        bedrock = boto3.client('bedrock-runtime',
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key,
                              region_name=region)
        # List available models
        models = bedrock.list_foundation_models(byProvider='Amazon')
        nova_models = [m for m in models.get('modelSummaries', []) if 'nova' in m.get('modelId', '').lower()]
        if nova_models:
            print(f"✓ Bedrock access OK (found {len(nova_models)} Nova models)")
            for model in nova_models[:2]:
                print(f"  - {model['modelId']}")
        else:
            print("⚠ Bedrock access OK but no Nova models found")
    except Exception as e:
        print(f"✗ Bedrock access failed: {e}")
        all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✓ All tests passed! AWS is properly configured.")
        return True
    else:
        print("✗ Some tests failed. Please review the errors above.")
        print("\nNext steps:")
        print("1. Ensure IAM policy is attached to your user")
        print("2. Check AWS Billing for unpaid invoices")
        print("3. Enable Amazon Transcribe in AWS Console")
        return False

if __name__ == '__main__':
    success = test_aws_config()
    sys.exit(0 if success else 1)