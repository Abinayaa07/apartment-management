from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from core.tasks import send_bulk_notification_task, send_user_notification_task


def send_user_notification(user, subject, message, html_template=None, context=None):
    if not user.email:
        return False

    html_message = None
    if html_template:
        html_message = render_to_string(html_template, context or {})

    try:
        send_user_notification_task.delay(user.email, subject, message, html_message)
    except Exception:
        send_user_notification_task.run(user.email, subject, message, html_message)
    return True


def send_bulk_notification(emails, subject, message, html_template=None, context=None):
    recipients = [email for email in emails if email]
    if not recipients:
        return 0

    html_message = None
    if html_template:
        html_message = render_to_string(html_template, context or {})

    try:
        send_bulk_notification_task.delay(recipients, subject, message, html_message)
    except Exception:
        send_bulk_notification_task.run(recipients, subject, message, html_message)
    return len(recipients)


def _absolute_url(request, route_name):
    path = reverse(route_name)
    if request is None:
        return path
    return request.build_absolute_uri(path)


def send_registration_notification(request, user):
    subject = "Welcome to AMS Apartment"
    registered_on = timezone.localtime(user.date_joined).strftime("%d %b %Y, %I:%M %p")
    login_link = _absolute_url(request, "login")
    message = (
        f"Hello {user.username},\n\n"
        "Welcome to AMS Apartment! Your account has been successfully created.\n\n"
        "Account Details:\n\n"
        f"Username: {user.username}\n"
        f"Email: {user.email or 'Not provided'}\n"
        f"Registered On: {registered_on}\n\n"
        "You can now log in and start using our services once your account is active.\n\n"
        f"Login here: {login_link}\n\n"
        "If you did not register for this account, please contact support immediately.\n\n"
        "Best regards,\n"
        "AMS Apartment Team"
    )
    return send_user_notification(
        user,
        subject,
        message,
        "emails/registration_email.html",
        {
            "subject": subject,
            "header_title": "Welcome to AMS Apartment",
            "header_copy": "Your account is ready and your registration details are below.",
            "user_name": user.username,
            "username": user.username,
            "email": user.email or "Not provided",
            "registered_date": registered_on,
            "action_label": "Login",
            "action_url": login_link,
        },
    )


def send_login_notification(request, user):
    subject = "Login Alert - AMS Apartment"
    login_time = timezone.localtime().strftime("%d %b %Y, %I:%M %p")
    message = (
        f"Hello {user.username},\n\n"
        "We detected a login to your AMS Apartment account.\n\n"
        "Login Details:\n\n"
        f"Date & Time: {login_time}\n"
        f"Role: {user.get_role_display()}\n\n"
        "If this was you, no action is required.\n\n"
        "If you do not recognize this activity, please reset your password immediately.\n\n"
        "Stay secure,\n"
        "AMS Apartment Team"
    )
    return send_user_notification(
        user,
        subject,
        message,
        "emails/login_alert_email.html",
        {
            "subject": subject,
            "header_title": "Login Alert",
            "header_copy": "A sign-in was detected on your account.",
            "user_name": user.username,
            "login_time": login_time,
            "role": user.get_role_display(),
        },
    )


def send_ticket_created_notification(request, user, ticket):
    subject = f"Ticket Created - #{ticket.id}"
    created_on = timezone.localtime(ticket.created_at).strftime("%d %b %Y, %I:%M %p")
    ticket_link = _absolute_url(request, "my_tickets")
    message = (
        f"Hello {user.username},\n\n"
        "Your ticket has been successfully created.\n\n"
        "Ticket Details:\n\n"
        f"Ticket ID: {ticket.id}\n"
        f"Subject: {ticket.title}\n"
        f"Priority: Standard\n"
        f"Status: {ticket.get_status_display()}\n"
        f"Created On: {created_on}\n\n"
        "Our team will review your request and respond shortly.\n\n"
        f"Track your ticket: {ticket_link}\n\n"
        "Thank you,\n"
        "Support Team\n"
        "AMS Apartment"
    )
    return send_user_notification(
        user,
        subject,
        message,
        "emails/ticket_created_email.html",
        {
            "subject": subject,
            "header_title": "Ticket Created",
            "header_copy": "Your maintenance request has been received by the system.",
            "user_name": user.username,
            "ticket_id": ticket.id,
            "ticket_subject": ticket.title,
            "priority": "Standard",
            "status": ticket.get_status_display(),
            "created_date": created_on,
            "action_label": "Track Ticket",
            "action_url": ticket_link,
        },
    )


def send_payment_success_notification(request, user, payment, payment_method="Recorded in AMS Apartment"):
    subject = f"Payment Successful - {payment.transaction_id or payment.id}"
    payment_date = timezone.localtime(payment.created_at).strftime("%d %b %Y, %I:%M %p")
    message = (
        f"Hello {user.username},\n\n"
        "Your payment has been successfully completed.\n\n"
        "Payment Details:\n\n"
        f"Amount Paid: INR {payment.amount}\n"
        f"Payment ID: {payment.transaction_id or payment.id}\n"
        f"Payment Method: {payment_method}\n"
        f"Date: {payment_date}\n\n"
        "Summary:\n\n"
        f"Service: Maintenance dues for {payment.month} {payment.year}\n"
        f"Status: {payment.get_status_display()}\n\n"
        "If you have any questions, feel free to contact us.\n\n"
        "Thank you for your payment!\n"
        "Billing Team\n"
        "AMS Apartment"
    )
    return send_user_notification(
        user,
        subject,
        message,
        "emails/payment_success_email.html",
        {
            "subject": subject,
            "header_title": "Payment Successful",
            "header_copy": "Your maintenance payment has been confirmed successfully.",
            "user_name": user.username,
            "amount": payment.amount,
            "payment_id": payment.transaction_id or payment.id,
            "payment_method": payment_method,
            "payment_date": payment_date,
            "service_name": f"Maintenance dues for {payment.month} {payment.year}",
            "status": payment.get_status_display(),
        },
    )


def send_new_due_notification(request, payment):
    user = payment.resident
    subject = "New Due Generated - Payment Required"
    payment_link = _absolute_url(request, "my_dues")
    message = (
        f"Hello {user.username},\n\n"
        "A new due has been generated for your AMS Apartment account.\n\n"
        "Due Details:\n\n"
        f"Amount: INR {payment.amount}\n"
        f"Due Date: {payment.month} {payment.year}\n"
        "Description: Maintenance dues\n\n"
        "Please complete the payment before the due date to avoid late fees.\n\n"
        f"Pay Now: {payment_link}\n\n"
        "Thank you,\n"
        "Accounts Team\n"
        "AMS Apartment"
    )
    return send_user_notification(
        user,
        subject,
        message,
        "emails/new_due_email.html",
        {
            "subject": subject,
            "header_title": "New Due Generated",
            "header_copy": "A new maintenance due has been added to your account.",
            "user_name": user.username,
            "due_amount": payment.amount,
            "due_date": f"{payment.month} {payment.year}",
            "description": "Maintenance dues",
            "action_label": "Pay Now",
            "action_url": payment_link,
        },
    )


def send_notice_created_notification(notice, recipients):
    subject = f"New Notice - {notice.title}"
    published_on = timezone.localtime(notice.created_at).strftime("%d %b %Y, %I:%M %p")
    message = (
        "Hello,\n\n"
        "A new notice has been published in AMS Apartment.\n\n"
        "Notice Details:\n\n"
        f"Title: {notice.title}\n"
        f"Audience: {notice.get_audience_display()}\n"
        f"Published On: {published_on}\n\n"
        f"Message:\n{notice.message}\n\n"
        "Please log in to the AMS Apartment portal to review it.\n\n"
        "AMS Apartment Team"
    )
    return send_bulk_notification(
        recipients,
        subject,
        message,
        "emails/notice_created_email.html",
        {
            "subject": subject,
            "header_title": "New Notice Published",
            "header_copy": "A new update has been posted to the apartment portal.",
            "notice_title": notice.title,
            "audience": notice.get_audience_display(),
            "published_on": published_on,
            "notice_message": notice.message,
        },
    )
