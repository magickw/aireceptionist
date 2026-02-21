# Voice Recognition Issue - Root Cause and Solution

## Problem
The call simulator shows "Nova could not understand the audio" error when trying to use voice input.

## Root Cause Analysis

### Primary Issue: Streaming Mode Fails
The code attempts to use AWS Nova Sonic v1's bidirectional streaming API first:
- This requires `boto3 >= 1.35.80`
- The `invoke_model_with_bidirectional_stream` method must be available
- If this fails, it falls back to batch mode

### Secondary Issue: Batch Mode Requires S3
When streaming mode fails, the batch mode is used:
1. Uploads audio to S3 bucket
2. Creates Amazon Transcribe job
3. Polls for transcription result

This requires:
- AWS credentials with S3 and Transcribe permissions
- Ability to create/access S3 bucket `aireceptionist-transcribe-{region}`

### Current State
- Local environment: AWS credentials not configured
- Production (Render): AWS credentials may not be configured or have insufficient permissions

## Solutions

### Option 1: Configure AWS Credentials (Recommended)
Add these environment variables to Render:

```bash
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
```

The IAM user/role needs these permissions:
- `s3:*` (for S3 bucket operations)
- `transcribe:*` (for transcription jobs)

### Option 2: Pre-create S3 Bucket
Create the S3 bucket manually to avoid permission issues:

```bash
aws s3 mb s3://aireceptionist-transcribe-us-east-1
```

### Option 3: Improve Error Handling
Add better error messages when voice mode fails and guide users to use text input.

### Option 4: Use Local STT (Development Only)
For local development, use a local STT library instead of AWS Transcribe.

## Immediate Workaround
Users can use the **Text Input** mode in the call simulator (toggle button next to microphone) as a workaround while voice is being fixed.

## Next Steps
1. Verify AWS credentials are configured in Render
2. Check IAM permissions for S3 and Transcribe
3. Test streaming mode initialization with proper boto3 version
4. Consider using a more reliable STT service for production
