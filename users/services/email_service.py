# users/services/email_service.py

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings


class EmailService:
    """
    Handles secure onboarding emails.
    Uses Django password reset token system.
    """

    @staticmethod
    def send_password_setup_email(user):

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            }
        )

        full_link = f"{settings.SITE_URL}{reset_link}"

        subject = "TESDA PCVMS Account Created – Action Required"

        message = f"""
Good day {user.get_full_name()},

Your TESDA PCVMS account has been created.

Entity: {user.entity.name}
Role(s): {", ".join(user.get_roles())}

Please click the link below to set your password:

{full_link}

This link will expire automatically.

If you did not expect this email, please contact your Administrator.

Thank you.
TESDA PCVMS System
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )