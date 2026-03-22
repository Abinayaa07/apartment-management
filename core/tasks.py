from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


@shared_task(ignore_result=True)
def send_user_notification_task(email, subject, message, html_message=None):
    if not email:
        return False

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    if html_message:
        email_message.attach_alternative(html_message, "text/html")
    email_message.send(fail_silently=True)
    return True


@shared_task(ignore_result=True)
def send_bulk_notification_task(emails, subject, message, html_message=None):
    sent = 0
    for email in emails:
        if not email:
            continue

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        if html_message:
            email_message.attach_alternative(html_message, "text/html")
        email_message.send(fail_silently=True)
        sent += 1

    return sent
