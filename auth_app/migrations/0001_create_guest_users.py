from django.contrib.auth.hashers import make_password
from django.db import migrations

# Guest logins used by the frontend (see GUEST_LOGINS in config.js)
GUEST_USERS = [
    {'username': 'andrey', 'password': 'asdasd', 'type': 'customer'},
    {'username': 'kevin', 'password': 'asdasd24', 'type': 'business'},
]


def create_guest_users(apps, schema_editor):
    """Creates the guest users together with their profiles."""
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('profiles_app', 'UserProfile')
    for guest in GUEST_USERS:
        user, created = User.objects.get_or_create(
            username=guest['username'],
            defaults={'password': make_password(guest['password'])},
        )
        UserProfile.objects.get_or_create(
            user=user, defaults={'type': guest['type']}
        )


def delete_guest_users(apps, schema_editor):
    """Removes the guest users again (the profiles are deleted via CASCADE)."""
    User = apps.get_model('auth', 'User')
    usernames = [guest['username'] for guest in GUEST_USERS]
    User.objects.filter(username__in=usernames).delete()


class Migration(migrations.Migration):

    # authtoken is needed so that deleting the guests also deletes their tokens
    dependencies = [
        ('profiles_app', '0001_initial'),
        ('authtoken', '0004_alter_tokenproxy_options'),
    ]

    operations = [
        migrations.RunPython(create_guest_users, delete_guest_users),
    ]
