"""
Call Recording Service
Call recording, storage, playback, and compliance management
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import boto3
import os
from botocore.exceptions import ClientError

from app.core.config import settings


class RecordingConsentType:
    """Recording consent types"""
    EXPLICIT = "explicit"  # Customer explicitly agreed
    IMPLIED = "implied"    # Consent implied by continuing call
    NOTIFICATION = "notification"  # Customer notified but no objection
    NONE = "none"          # No consent obtained


class CallRecordingService:
    """Service for call recording management"""
    
    # Recording storage settings
    RECORDING_BUCKET = os.getenv('RECORDING_BUCKET', 'receptium-recordings')
    RECORDING_FORMAT = 'mp3'
    RETENTION_DAYS = 90  # Default retention period
    
    # Compliance settings by region
    COMPLIANCE_RULES = {
        'US': {
            'consent_required': 'one_party',  # one_party or all_party
            'notification_required': False,
            'retention_minimum_days': 30,
            'encryption_required': True
        },
        'EU': {
            'consent_required': 'all_party',
            'notification_required': True,
            'retention_minimum_days': 90,
            'encryption_required': True
        },
        'UK': {
            'consent_required': 'one_party',
            'notification_required': True,
            'retention_minimum_days': 30,
            'encryption_required': True
        },
        'CA': {
            'consent_required': 'one_party',
            'notification_required': True,
            'retention_minimum_days': 30,
            'encryption_required': True
        },
        'AU': {
            'consent_required': 'all_party',
            'notification_required': True,
            'retention_minimum_days': 30,
            'encryption_required': True
        }
    }
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.transcribe_client = boto3.client(
            'transcribe',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    def start_recording(
        self,
        db: Session,
        call_session_id: str,
        business_id: int,
        region: str = 'US'
    ) -> Dict:
        """Start recording a call session"""
        from app.models.models import CallSession, CallRecording
        
        # Check compliance rules
        compliance = self.COMPLIANCE_RULES.get(region, self.COMPLIANCE_RULES['US'])
        
        # Generate recording key
        timestamp = datetime.now(timezone.utc).strftime('%Y/%m/%d')
        recording_key = f"{business_id}/{timestamp}/{call_session_id}.{self.RECORDING_FORMAT}"
        
        # Create recording record
        recording = CallRecording(
            call_session_id=call_session_id,
            business_id=business_id,
            recording_key=recording_key,
            status="recording",
            started_at=datetime.now(timezone.utc),
            consent_type=RecordingConsentType.NONE,
            compliance_region=region,
            encryption_enabled=compliance.get('encryption_required', True)
        )
        
        db.add(recording)
        db.commit()
        db.refresh(recording)
        
        return {
            "recording_id": recording.id,
            "status": "recording",
            "recording_key": recording_key,
            "consent_required": compliance['consent_required'],
            "notification_required": compliance['notification_required']
        }
    
    def stop_recording(
        self,
        db: Session,
        call_session_id: str,
        recording_data: bytes = None
    ) -> Dict:
        """Stop recording and save to storage"""
        from app.models.models import CallRecording
        
        recording = db.query(CallRecording).filter(
            CallRecording.call_session_id == call_session_id,
            CallRecording.status == "recording"
        ).first()
        
        if not recording:
            return {"error": "No active recording found"}
        
        try:
            # Upload to S3
            if recording_data:
                self.s3_client.put_object(
                    Bucket=self.RECORDING_BUCKET,
                    Key=recording.recording_key,
                    Body=recording_data,
                    ContentType=f'audio/{self.RECORDING_FORMAT}',
                    ServerSideEncryption='aws:kms'
                )
            
            # Update recording record
            recording.status = "completed"
            recording.ended_at = datetime.now(timezone.utc)
            recording.duration_seconds = int(
                (recording.ended_at - recording.started_at).total_seconds()
            )
            recording.file_size_bytes = len(recording_data) if recording_data else 0
            
            db.commit()
            
            return {
                "recording_id": recording.id,
                "status": "completed",
                "duration_seconds": recording.duration_seconds,
                "recording_key": recording.recording_key
            }
            
        except ClientError as e:
            recording.status = "failed"
            recording.error_message = str(e)
            db.commit()
            return {"error": f"Failed to save recording: {e}"}
    
    def record_consent(
        self,
        db: Session,
        call_session_id: str,
        consent_type: str,
        consent_method: str = "verbal"
    ) -> Dict:
        """Record customer consent for call recording"""
        from app.models.models import CallRecording
        
        recording = db.query(CallRecording).filter(
            CallRecording.call_session_id == call_session_id
        ).order_by(CallRecording.started_at.desc()).first()
        
        if not recording:
            return {"error": "No recording found"}
        
        recording.consent_type = consent_type
        recording.consent_obtained_at = datetime.now(timezone.utc)
        recording.consent_method = consent_method
        
        db.commit()
        
        return {
            "recording_id": recording.id,
            "consent_type": consent_type,
            "consent_recorded": True
        }
    
    def get_recording_url(
        self,
        db: Session,
        recording_id: int,
        expiry_hours: int = 24
    ) -> Dict:
        """Generate a presigned URL for recording playback"""
        from app.models.models import CallRecording
        
        recording = db.query(CallRecording).filter(
            CallRecording.id == recording_id
        ).first()
        
        if not recording:
            return {"error": "Recording not found"}
        
        if recording.status != "completed":
            return {"error": "Recording not ready"}
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.RECORDING_BUCKET,
                    'Key': recording.recording_key
                },
                ExpiresIn=expiry_hours * 3600
            )
            
            return {
                "recording_id": recording_id,
                "url": url,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=expiry_hours)).isoformat(),
                "duration_seconds": recording.duration_seconds
            }
            
        except ClientError as e:
            return {"error": f"Failed to generate URL: {e}"}
    
    def get_call_recordings(
        self,
        db: Session,
        business_id: int,
        call_session_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get recordings for a business"""
        from app.models.models import CallRecording
        
        query = db.query(CallRecording).filter(
            CallRecording.business_id == business_id
        )
        
        if call_session_id:
            query = query.filter(CallRecording.call_session_id == call_session_id)
        
        if start_date:
            query = query.filter(CallRecording.started_at >= start_date)
        
        if end_date:
            query = query.filter(CallRecording.started_at <= end_date)
        
        recordings = query.order_by(CallRecording.started_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "call_session_id": r.call_session_id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                "duration_seconds": r.duration_seconds,
                "status": r.status,
                "consent_type": r.consent_type,
                "has_transcript": bool(r.transcript_key)
            }
            for r in recordings
        ]
    
    def transcribe_recording(
        self,
        db: Session,
        recording_id: int
    ) -> Dict:
        """Transcribe a recording using AWS Transcribe"""
        from app.models.models import CallRecording
        
        recording = db.query(CallRecording).filter(
            CallRecording.id == recording_id
        ).first()
        
        if not recording:
            return {"error": "Recording not found"}
        
        if recording.status != "completed":
            return {"error": "Recording not ready for transcription"}
        
        try:
            # Start transcription job
            job_name = f"transcribe-{recording_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            transcript_key = f"transcripts/{recording.recording_key.replace('.mp3', '.json')}"
            
            job = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={
                    'MediaFileUri': f"s3://{self.RECORDING_BUCKET}/{recording.recording_key}"
                },
                MediaFormat=self.RECORDING_FORMAT,
                LanguageCode='en-US',
                OutputBucketName=self.RECORDING_BUCKET,
                OutputKey=transcript_key,
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 2
                }
            )
            
            # Update recording with transcript info
            recording.transcript_job_name = job_name
            recording.transcript_key = transcript_key
            recording.transcript_status = "processing"
            db.commit()
            
            return {
                "recording_id": recording_id,
                "transcript_job_name": job_name,
                "status": "processing"
            }
            
        except ClientError as e:
            return {"error": f"Transcription failed: {e}"}
    
    def get_transcript(
        self,
        db: Session,
        recording_id: int
    ) -> Dict:
        """Get transcript for a recording"""
        from app.models.models import CallRecording
        
        recording = db.query(CallRecording).filter(
            CallRecording.id == recording_id
        ).first()
        
        if not recording:
            return {"error": "Recording not found"}
        
        if not recording.transcript_key:
            return {"error": "No transcript available"}
        
        try:
            # Get transcript from S3
            response = self.s3_client.get_object(
                Bucket=self.RECORDING_BUCKET,
                Key=recording.transcript_key
            )
            
            transcript_data = json.loads(response['Body'].read())
            
            # Parse transcript
            results = transcript_data.get('results', {})
            transcript_text = ' '.join([
                item['alternatives'][0]['content']
                for item in results.get('items', [])
                if item.get('alternatives')
            ])
            
            # Update recording status
            recording.transcript_status = "completed"
            db.commit()
            
            return {
                "recording_id": recording_id,
                "transcript": transcript_text,
                "speakers": results.get('speaker_labels', {}),
                "items": results.get('items', [])
            }
            
        except ClientError as e:
            return {"error": f"Failed to get transcript: {e}"}
    
    def delete_recording(
        self,
        db: Session,
        recording_id: int,
        reason: str = None
    ) -> Dict:
        """Delete a recording (for compliance/GDPR)"""
        from app.models.models import CallRecording
        
        recording = db.query(CallRecording).filter(
            CallRecording.id == recording_id
        ).first()
        
        if not recording:
            return {"error": "Recording not found"}
        
        try:
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.RECORDING_BUCKET,
                Key=recording.recording_key
            )
            
            if recording.transcript_key:
                self.s3_client.delete_object(
                    Bucket=self.RECORDING_BUCKET,
                    Key=recording.transcript_key
                )
            
            # Soft delete in database
            recording.status = "deleted"
            recording.deleted_at = datetime.now(timezone.utc)
            recording.deletion_reason = reason
            recording.recording_key = None
            recording.transcript_key = None
            
            db.commit()
            
            return {
                "recording_id": recording_id,
                "status": "deleted"
            }
            
        except ClientError as e:
            return {"error": f"Failed to delete recording: {e}"}
    
    def get_retention_policy(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Get recording retention policy for a business"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        
        default_policy = {
            "retention_days": self.RETENTION_DAYS,
            "auto_delete": True,
            "encrypt_at_rest": True,
            "consent_required": "one_party"
        }
        
        if business and business.settings:
            return {
                **default_policy,
                **business.settings.get('recording_policy', {})
            }
        
        return default_policy
    
    def check_retention_compliance(
        self,
        db: Session,
        business_id: int
    ) -> Dict:
        """Check for recordings that need to be deleted based on retention policy"""
        from app.models.models import CallRecording
        
        policy = self.get_retention_policy(db, business_id)
        retention_days = policy.get('retention_days', self.RETENTION_DAYS)
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Find recordings past retention
        old_recordings = db.query(CallRecording).filter(
            CallRecording.business_id == business_id,
            CallRecording.status == "completed",
            CallRecording.started_at < cutoff_date
        ).all()
        
        return {
            "recordings_to_delete": len(old_recordings),
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
            "recording_ids": [r.id for r in old_recordings]
        }
    
    def get_consent_notification_message(
        self,
        region: str = 'US'
    ) -> str:
        """Get the appropriate consent notification message for a region"""
        compliance = self.COMPLIANCE_RULES.get(region, self.COMPLIANCE_RULES['US'])
        
        if compliance['consent_required'] == 'all_party':
            return "This call may be recorded for quality and training purposes. By continuing this call, you consent to being recorded."
        else:
            return "This call may be recorded for quality and training purposes."


# Singleton instance
call_recording_service = CallRecordingService()
