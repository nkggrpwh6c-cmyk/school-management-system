from django.db import migrations


def create_default_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    # Admin
    admin_username = 'admin'
    admin_password = 'admin123'
    if not User.objects.filter(username=admin_username).exists():
        admin = User.objects.create(username=admin_username, is_staff=True, is_superuser=True)
        admin.set_password(admin_password)
        admin.save()

    # Registrar account
    registrar_username = 'crenz'
    registrar_password = 'crenz123'
    registrar_defaults = {
        'email': '',
        'is_staff': True,
        'is_superuser': False,
    }
    registrar, _ = User.objects.get_or_create(username=registrar_username, defaults=registrar_defaults)
    registrar.set_password(registrar_password)
    # If the custom User model has a role field, set ADMIN
    try:
        setattr(registrar, 'role', 'ADMIN')
    except Exception:
        pass
    registrar.save()


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


