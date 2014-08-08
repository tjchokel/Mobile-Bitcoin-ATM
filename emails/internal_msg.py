from django.core.mail import send_mail

from bitcash.settings import ADMINS, SERVER_EMAIL, EMAIL_DEV_PREFIX


def send_internal_email(subject, message, recipient_list=None):
    " Send an admin email "

    if not recipient_list:
        recipient_list = [x[1] for x in ADMINS]

    if EMAIL_DEV_PREFIX:
        subject += ' [DEV]'

    send_mail(
            subject=subject,
            message=message,
            from_email=SERVER_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            )
