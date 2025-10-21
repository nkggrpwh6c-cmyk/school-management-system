from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    # Admin account
    admin_username = 'admin'
    admin_password = 'admin123'
    if not User.objects.filter(username=admin_username).exists():
        User.objects.create(
            username=admin_username,
            email='admin@vbca.edu',
            password=make_password(admin_password),
            first_name='System',
            last_name='Administrator',
            is_staff=True,
            is_superuser=True
        )

    # Registrar account
    registrar_username = 'crenz'
    registrar_password = 'crenz123'
    if not User.objects.filter(username=registrar_username).exists():
        User.objects.create(
            username=registrar_username,
            email='crenz@vbca.edu',
            password=make_password(registrar_password),
            first_name='Registrar',
            last_name='Administrator',
            is_staff=True,
            is_superuser=False
        )

    # Security Admin account
    security_username = 'security_admin'
    security_password = 'security123'
    if not User.objects.filter(username=security_username).exists():
        User.objects.create(
            username=security_username,
            email='security@vbca.edu',
            password=make_password(security_password),
            first_name='Security',
            last_name='Administrator',
            is_staff=True,
            is_superuser=True
        )


def noop(apps, schema_editor):
    # No reverse operation; users can be deleted manually if needed
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_users, noop),
    ]


