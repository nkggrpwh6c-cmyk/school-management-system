"""
Auto Backup and Data Encryption System
"""
import os
import json
import zipfile
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from cryptography.fernet import Fernet
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
import logging

logger = logging.getLogger(__name__)

class DataEncryption:
    """Handle data encryption and decryption"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Get or create encryption key"""
        key_file = os.path.join(settings.BASE_DIR, 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def encrypt_data(self, data):
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data).decode('utf-8')

class CloudBackupManager:
    """Manage cloud backups"""
    
    def __init__(self):
        self.s3_client = None
        self.bucket_name = getattr(settings, 'BACKUP_S3_BUCKET', None)
        self._initialize_s3()
    
    def _initialize_s3(self):
        """Initialize S3 client"""
        if not AWS_AVAILABLE:
            logger.warning("AWS SDK not available, cloud backup disabled")
            return
            
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
    
    def upload_backup(self, backup_file_path, backup_name):
        """Upload backup to S3"""
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3 not configured, skipping cloud backup")
            return False
        
        try:
            self.s3_client.upload_file(
                backup_file_path,
                self.bucket_name,
                f"backups/{backup_name}"
            )
            logger.info(f"Backup uploaded to S3: {backup_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            return False
    
    def download_backup(self, backup_name, local_path):
        """Download backup from S3"""
        if not self.s3_client or not self.bucket_name:
            return False
        
        try:
            self.s3_client.download_file(
                self.bucket_name,
                f"backups/{backup_name}",
                local_path
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to download backup from S3: {e}")
            return False

class BackupManager:
    """Main backup management system"""
    
    def __init__(self):
        self.encryption = DataEncryption()
        self.cloud_manager = CloudBackupManager()
        self.backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, mode=0o700)
    
    def create_backup(self, backup_type='full'):
        """Create a backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{backup_type}_{timestamp}"
        
        try:
            # Create backup data
            backup_data = self._collect_backup_data(backup_type)
            
            # Encrypt backup data
            encrypted_data = self.encryption.encrypt_data(json.dumps(backup_data))
            
            # Create backup file
            backup_file_path = os.path.join(self.backup_dir, f"{backup_name}.enc")
            with open(backup_file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Create metadata
            metadata = {
                'backup_name': backup_name,
                'backup_type': backup_type,
                'created_at': timezone.now().isoformat(),
                'file_size': os.path.getsize(backup_file_path),
                'checksum': self._calculate_checksum(backup_file_path),
                'encrypted': True
            }
            
            metadata_file = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload to cloud
            self.cloud_manager.upload_backup(backup_file_path, f"{backup_name}.enc")
            self.cloud_manager.upload_backup(metadata_file, f"{backup_name}_metadata.json")
            
            logger.info(f"Backup created successfully: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _collect_backup_data(self, backup_type):
        """Collect data for backup"""
        from apps.students.models import Student
        from apps.documents.sf10_models import SF10Document
        from apps.accounts.models import User
        from django.contrib.auth.models import Group, Permission
        
        backup_data = {
            'backup_info': {
                'created_at': timezone.now().isoformat(),
                'backup_type': backup_type,
                'django_version': settings.DJANGO_VERSION,
            },
            'users': [],
            'students': [],
            'sf10_documents': [],
            'groups': [],
            'permissions': []
        }
        
        # Backup users
        for user in User.objects.all():
            backup_data['users'].append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'role': user.role,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            })
        
        # Backup students
        for student in Student.objects.all():
            backup_data['students'].append({
                'student_id': student.student_id,
                'user_id': student.user.id,
                'lrn': student.lrn,
                'contact_number': student.contact_number,
                'address': student.address,
                'birth_date': student.birth_date.isoformat() if student.birth_date else None,
                'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
                'is_active': student.is_active,
                'grade_id': student.grade.id if student.grade else None,
                'section_id': student.section.id if student.section else None,
                'created_at': student.created_at.isoformat(),
                'updated_at': student.updated_at.isoformat(),
            })
        
        # Backup SF10 documents
        for sf10 in SF10Document.objects.all():
            backup_data['sf10_documents'].append({
                'id': sf10.id,
                'student_id': sf10.student.student_id,
                'school_year': sf10.school_year,
                'grade_level': sf10.grade_level,
                'section': sf10.section,
                'lrn': sf10.lrn,
                'name': sf10.name,
                'birth_date': sf10.birth_date.isoformat(),
                'birth_place': sf10.birth_place,
                'sex': sf10.sex,
                'age': sf10.age,
                'present_address': sf10.present_address,
                'permanent_address': sf10.permanent_address,
                'contact_number': sf10.contact_number,
                'email': sf10.email,
                'father_name': sf10.father_name,
                'father_occupation': sf10.father_occupation,
                'father_contact': sf10.father_contact,
                'mother_name': sf10.mother_name,
                'mother_occupation': sf10.mother_occupation,
                'mother_contact': sf10.mother_contact,
                'guardian_name': sf10.guardian_name,
                'guardian_relationship': sf10.guardian_relationship,
                'guardian_contact': sf10.guardian_contact,
                'previous_school': sf10.previous_school,
                'previous_grade': sf10.previous_grade,
                'date_of_enrollment': sf10.date_of_enrollment.isoformat(),
                'date_of_graduation': sf10.date_of_graduation.isoformat() if sf10.date_of_graduation else None,
                'status': sf10.status,
                'is_complete': sf10.is_complete,
                'notes': sf10.notes,
                'created_by_id': sf10.created_by.id,
                'created_at': sf10.created_at.isoformat(),
                'updated_at': sf10.updated_at.isoformat(),
            })
        
        # Backup groups and permissions
        for group in Group.objects.all():
            backup_data['groups'].append({
                'id': group.id,
                'name': group.name,
                'permissions': list(group.permissions.values_list('id', flat=True))
            })
        
        for permission in Permission.objects.all():
            backup_data['permissions'].append({
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename,
                'content_type_id': permission.content_type_id
            })
        
        return backup_data
    
    def _calculate_checksum(self, file_path):
        """Calculate file checksum"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def restore_backup(self, backup_name):
        """Restore from backup"""
        try:
            # Download from cloud if needed
            backup_file_path = os.path.join(self.backup_dir, f"{backup_name}.enc")
            metadata_file = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            
            if not os.path.exists(backup_file_path):
                self.cloud_manager.download_backup(f"{backup_name}.enc", backup_file_path)
            if not os.path.exists(metadata_file):
                self.cloud_manager.download_backup(f"{backup_name}_metadata.json", metadata_file)
            
            # Read and decrypt backup data
            with open(backup_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.encryption.decrypt_data(encrypted_data)
            backup_data = json.loads(decrypted_data)
            
            # Restore data
            self._restore_data(backup_data)
            
            logger.info(f"Backup restored successfully: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def _restore_data(self, backup_data):
        """Restore data from backup"""
        from apps.students.models import Student
        from apps.documents.sf10_models import SF10Document
        from apps.accounts.models import User
        from django.contrib.auth.models import Group, Permission
        
        with transaction.atomic():
            # Restore users
            for user_data in backup_data.get('users', []):
                user, created = User.objects.get_or_create(
                    id=user_data['id'],
                    defaults={
                        'username': user_data['username'],
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'is_active': user_data['is_active'],
                        'is_staff': user_data['is_staff'],
                        'is_superuser': user_data['is_superuser'],
                        'role': user_data['role'],
                    }
                )
                if not created:
                    # Update existing user
                    for field in ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'role']:
                        setattr(user, field, user_data[field])
                    user.save()
            
            # Restore students
            for student_data in backup_data.get('students', []):
                try:
                    user = User.objects.get(id=student_data['user_id'])
                    student, created = Student.objects.get_or_create(
                        student_id=student_data['student_id'],
                        defaults={
                            'user': user,
                            'lrn': student_data['lrn'],
                            'contact_number': student_data['contact_number'],
                            'address': student_data['address'],
                            'is_active': student_data['is_active'],
                        }
                    )
                    if not created:
                        # Update existing student
                        for field in ['lrn', 'contact_number', 'address', 'is_active']:
                            setattr(student, field, student_data[field])
                        student.save()
                except User.DoesNotExist:
                    logger.warning(f"User not found for student {student_data['student_id']}")
    
    def cleanup_old_backups(self, days_to_keep=30):
        """Clean up old backup files"""
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for filename in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old backup files")
        return cleaned_count

class BackupScheduler:
    """Schedule automatic backups"""
    
    @staticmethod
    def run_daily_backup():
        """Run daily backup"""
        backup_manager = BackupManager()
        backup_name = backup_manager.create_backup('daily')
        
        if backup_name:
            # Clean up old backups
            backup_manager.cleanup_old_backups()
            logger.info(f"Daily backup completed: {backup_name}")
        else:
            logger.error("Daily backup failed")
    
    @staticmethod
    def run_weekly_backup():
        """Run weekly backup"""
        backup_manager = BackupManager()
        backup_name = backup_manager.create_backup('weekly')
        
        if backup_name:
            logger.info(f"Weekly backup completed: {backup_name}")
        else:
            logger.error("Weekly backup failed")
    
    @staticmethod
    def run_monthly_backup():
        """Run monthly backup"""
        backup_manager = BackupManager()
        backup_name = backup_manager.create_backup('monthly')
        
        if backup_name:
            logger.info(f"Monthly backup completed: {backup_name}")
        else:
            logger.error("Monthly backup failed")
