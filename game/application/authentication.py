from django.contrib.auth.models import User

from game.services.supabase_auth import get_or_create_local_user, sign_in, sign_up


def register_with_supabase(email, password, username_hint):
    identity = sign_up(email, password)
    return get_or_create_local_user(identity, username_hint=username_hint)


def login_with_supabase(email_or_username, password):
    email = email_or_username
    if "@" not in email_or_username:
        user_by_name = User.objects.filter(username=email_or_username).first()
        email = user_by_name.email if user_by_name and user_by_name.email else email_or_username
    identity = sign_in(email, password)
    return get_or_create_local_user(identity, username_hint=email_or_username)
