from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured, ValidationError

from game.models import PlayerProfile


@dataclass(frozen=True)
class SupabaseIdentity:
    id: str
    email: str


class SupabaseAuthError(Exception):
    pass


def supabase_auth_is_enabled():
    return bool(settings.SUPABASE_AUTH_ENABLED)


def _client():
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ImproperlyConfigured("SUPABASE_URL and SUPABASE_ANON_KEY are required when Supabase auth is enabled.")
    from supabase import create_client

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def _identity_from_auth_response(response):
    user = getattr(response, "user", None)
    if not user:
        raise SupabaseAuthError("Supabase did not return a user.")
    email = getattr(user, "email", "") or ""
    user_id = getattr(user, "id", "") or ""
    if not email or not user_id:
        raise SupabaseAuthError("Supabase user payload is incomplete.")
    return SupabaseIdentity(id=user_id, email=email)


def sign_up(email, password):
    try:
        response = _client().auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"email_redirect_to": settings.SUPABASE_AUTH_REDIRECT_TO} if settings.SUPABASE_AUTH_REDIRECT_TO else {},
            }
        )
    except Exception as exc:
        raise SupabaseAuthError(str(exc)) from exc
    return _identity_from_auth_response(response)


def sign_in(email, password):
    try:
        response = _client().auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        raise SupabaseAuthError(str(exc)) from exc
    return _identity_from_auth_response(response)


def get_or_create_local_user(identity, username_hint=""):
    user = None
    profile = PlayerProfile.objects.filter(supabase_user_id=identity.id).select_related("user").first()
    if profile:
        return profile.user

    if identity.email:
        user = User.objects.filter(email__iexact=identity.email).first()
    if user is None and username_hint:
        user = User.objects.filter(username=username_hint).first()

    if user is None:
        username = _available_username(username_hint or identity.email.split("@")[0])
        user = User.objects.create_user(username=username, email=identity.email)
        user.set_unusable_password()
        user.save(update_fields=["password"])
    else:
        changed = []
        if identity.email and user.email != identity.email:
            user.email = identity.email
            changed.append("email")
        if user.has_usable_password():
            user.set_unusable_password()
            changed.append("password")
        if changed:
            user.save(update_fields=changed)

    profile, _created = PlayerProfile.objects.get_or_create(user=user)
    if profile.supabase_user_id and profile.supabase_user_id != identity.id:
        raise ValidationError("Этот локальный профиль уже связан с другим Supabase-пользователем.")
    profile.supabase_user_id = identity.id
    profile.save(update_fields=["supabase_user_id"])
    return user


def _available_username(raw_username):
    base = "".join(ch for ch in raw_username.strip() if ch.isalnum() or ch in "_-")[:30] or "player"
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base[:24]}-{suffix}"
    return username
