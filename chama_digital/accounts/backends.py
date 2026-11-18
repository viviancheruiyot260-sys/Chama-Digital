import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


def normalize_phone(value: str) -> str:
    digits = re.sub(r'\D+', '', value or '')
    if digits.startswith('0') and len(digits) == 10:
        digits = '254' + digits[1:]
    return digits


class EmailOrPhoneBackend(ModelBackend):
    """Allows members and officials to log in with either email or Kenyan phone number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = (username or kwargs.get(User.USERNAME_FIELD) or '').strip()
        if not identifier or not password:
            return None

        normalized_input = normalize_phone(identifier)
        candidates = User.objects.filter(
            Q(email__iexact=identifier)
            | Q(username__iexact=identifier)
            | Q(phone_number__iexact=identifier)
        )

        if not candidates.exists() and normalized_input:
            for u in User.objects.all():
                if normalize_phone(u.phone_number) == normalized_input:
                    candidates = [u]
                    break

        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
