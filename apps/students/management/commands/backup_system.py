"""
Management command for automated backup system
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.students.backup_system import BackupScheduler, BackupManager
from apps.students.archive_models import ArchiveManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run automated backup and maintenance tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'manual'],
            default='daily',
            help='Type of backup to run'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Run cleanup tasks'
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Run auto-archive tasks'
        )
    
    def handle(self, *args, **options):
        backup_type = options['type']
        run_cleanup = options['cleanup']
        run_archive = options['archive']
        
        self.stdout.write(f"Starting {backup_type} backup process...")
        
        try:
            # Run backup
            if backup_type == 'daily':
                BackupScheduler.run_daily_backup()
            elif backup_type == 'weekly':
                BackupScheduler.run_weekly_backup()
            elif backup_type == 'monthly':
                BackupScheduler.run_monthly_backup()
            elif backup_type == 'manual':
                backup_manager = BackupManager()
                backup_name = backup_manager.create_backup('manual')
                if backup_name:
                    self.stdout.write(
                        self.style.SUCCESS(f'Manual backup created: {backup_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Manual backup failed')
                    )
            
            # Run cleanup if requested
            if run_cleanup:
                self.stdout.write("Running cleanup tasks...")
                backup_manager = BackupManager()
                cleaned_count = backup_manager.cleanup_old_backups()
                self.stdout.write(f"Cleaned up {cleaned_count} old backup files")
                
                # Clean up old archives
                cleaned_archives = ArchiveManager.cleanup_old_archives()
                self.stdout.write(f"Cleaned up {cleaned_archives} old archive records")
            
            # Run auto-archive if requested
            if run_archive:
                self.stdout.write("Running auto-archive tasks...")
                archived_count = ArchiveManager.auto_archive_inactive_students()
                self.stdout.write(f"Auto-archived {archived_count} inactive students")
            
            self.stdout.write(
                self.style.SUCCESS(f'{backup_type.title()} backup completed successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )
            logger.error(f"Backup command failed: {str(e)}")
            raise
