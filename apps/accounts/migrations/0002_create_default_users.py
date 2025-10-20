from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    # Admin
    admin_username = 'admin'
    admin_password = 'admin123'
    if not User.objects.filter(username=admin_username).exists():
        User.objects.create(
            username=admin_username,
            password=make_password(admin_password),
            is_staff=True,
            is_superuser=True
        )

    # Registrar account
    registrar_username = 'crenz'
    registrar_password = 'crenz123'
    if not User.objects.filter(username=registrar_username).exists():
        registrar_defaults = {
            'email': '',
            'password': make_password(registrar_password),
            'is_staff': True,
            'is_superuser': False,
        }
        registrar = User.objects.create(username=registrar_username, **registrar_defaults)
        # If the custom User model has a role field, set ADMIN
        try:
            registrar.role = 'ADMIN'
            registrar.save(update_fields=['role'])
        except Exception:
            pass


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


