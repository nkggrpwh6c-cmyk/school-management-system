from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_default_users(apps, schema_editor):
    # Get the User model
    User = apps.get_model('accounts', 'User')

    # Create admin user
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            password=make_password('admin123'),
            is_staff=True,
            is_superuser=True
        )

    # Create security admin user
    if not User.objects.filter(username='security_admin').exists():
        User.objects.create(
            username='security_admin',
            password=make_password('security123'),
            is_staff=True,
            is_superuser=True
        )

    # Create registrar user
    if not User.objects.filter(username='crenz').exists():
        User.objects.create(
            username='crenz',
            password=make_password('crenz123'),
            is_staff=True,
            is_superuser=False
        )

def reverse_default_users(apps, schema_editor):
    # No reverse operation - users can be deleted manually if needed
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_users, reverse_default_users),
    ]
