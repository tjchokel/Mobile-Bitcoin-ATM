from django.core.mail import send_mail

from bitcash.settings import ADMINS, SERVER_EMAIL


def get_admin_emails():
    return [x[1] for x in ADMINS]


def send_admin_email(subject, message):
    send_mail(
            subject=subject,
            message=message,
            from_email=SERVER_EMAIL,  # TODO: different address for this
            recipient_list=get_admin_emails(),
            fail_silently=False,
            )
