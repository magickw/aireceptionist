# AWS Configuration for AI Receptionist

## Prerequisites

1. AWS Account with access to:
   - Amazon Transcribe (Streaming API)
   - Amazon S3 (for batch transcription fallback)
   - Amazon Bedrock (Nova 2 Lite, Nova Sonic)
   - Amazon Polly (text-to-speech)

2. IAM user or role with permissions

## Step 1: Create IAM Policy

Create a new IAM policy with the permissions in `IAM_POLICY_AWS_TRANSCRIBE_S3.json`:

```bash
aws iam create-policy \
  --policy-name AIReceptionistTranscribePolicy \
  --policy-document file://IAM_POLICY_AWS_TRANSCRIBE_S3.json
```

Or via AWS Console:
1. Go to IAM → Policies → Create policy
2. Choose JSON tab
3. Paste the content from `IAM_POLICY_AWS_TRANSCRIBE_S3.json`
4. Name it `AIReceptionistTranscribePolicy`

## Step 2: Attach Policy to IAM User

```bash
aws iam attach-user-policy \
  --user-name nova \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/AIReceptionistTranscribePolicy
```

Or via AWS Console:
1. Go to IAM → Users → nova
2. Add permissions → Attach existing policies
3. Select `AIReceptionistTranscribePolicy`

## Step 3: Enable Amazon Transcribe Subscription

### Via AWS Console:

1. Go to [Amazon Transcribe Console](https://console.aws.amazon.com/transcribe/)
2. Click "Get started" if first time, or navigate to Settings
3. Make sure the service is enabled for your region
4. Note: There may be additional subscription requirements for Streaming API

### Check Service Quotas:

```bash
aws service-quotas list-service-quotas \
  --service-code transcribe \
  --region us-east-1 \
  --query "Quotas[?QuotaCode=='StreamingConcurrentTranscriptions'].{QuotaName:QuotaName,Value:Value,Unit:Unit}"
```

## Step 4: Verify S3 Permissions

The policy includes permissions for the S3 bucket. If you prefer to use an existing bucket, update the Resource ARN:

```json
"Resource": [
  "arn:aws:s3:::YOUR_EXISTING_BUCKET",
  "arn:aws:s3:::YOUR_EXISTING_BUCKET/*"
]
```

## Step 5: Update Environment Variables

Ensure your backend has these environment variables:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

Or set in `.env` file:
```
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
AWS_REGION=us-east-1
```

## Step 6: Test Configuration

Run this test to verify AWS access:

```bash
cd backend
python3 << 'EOF'
import boto3
import os

from app.core.config import settings

# Test Transcribe Streaming
try:
    from amazon_transcribe.client import TranscribeStreamingClient
    client = TranscribeStreamingClient(region=settings.AWS_REGION)
    print("✓ Transcribe Streaming SDK available")
except ImportError:
    print("✗ amazon-transcribe SDK not installed")

# Test S3 Access
try:
    s3 = boto3.client('s3', region_name=settings.AWS_REGION)
    buckets = s3.list_buckets()
    print(f"✓ S3 access OK (found {len(buckets['Buckets'])} buckets)")
except Exception as e:
    print(f"✗ S3 access failed: {e}")

# Test Transcribe Service
try:
    transcribe = boto3.client('transcribe', region_name=settings.AWS_REGION)
    transcribe.list_transcription_jobs()
    print("✓ Transcribe service access OK")
except Exception as e:
    print(f"✗ Transcribe service access failed: {e}")
EOF
```

## Troubleshooting

### Issue: "SubscriptionRequiredException"

**Cause**: AWS account doesn't have Amazon Transcribe Streaming enabled

**Solution**:
1. Check AWS Billing for any unpaid invoices
2. Ensure your AWS account has an active payment method
3. Contact AWS Support to enable Transcribe Streaming

### Issue: "AccessDenied" for S3

**Cause**: IAM user lacks S3 permissions

**Solution**:
1. Verify policy is attached: `aws iam list-attached-user-policies --user-name nova`
2. Check policy ARN matches your account ID
3. Allow IAM changes to propagate (may take a few seconds)

### Issue: Transcribe SDK not found

**Install**:
```bash
cd backend
pip install amazon-transcribe
```

## Minimum Required Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:StartStreamTranscription",
        "transcribe:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::aireceptionist-transcribe-*",
        "arn:aws:s3:::aireceptionist-transcribe-*/*"
      ]
    }
  ]
}
```

## AWS Cost Considerations

- **Amazon Transcribe Streaming**: $0.024 per 15 seconds
- **Amazon Transcribe Batch**: $0.024 per minute (cheaper for longer recordings)
- **S3 Storage**: ~$0.023 per GB/month (minimal, only for temp files)
- **S3 Data Transfer**: Minimal for internal use

Estimated monthly cost for 100 hours of voice: ~$58