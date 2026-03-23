from __future__ import annotations

import html
import logging
import smtplib
from dataclasses import dataclass
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Formatter

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.common.utils import now_utc
from app.core.config import settings
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)

# ── Notification types ────────────────────────────────────────────────────────
TASK_CONFIRMED_NOTIFICATION             = "TASK_CONFIRMED"
CUSTOMER_VERIFICATION_NOTIFICATION     = "CUSTOMER_VERIFICATION"
VENDOR_VERIFICATION_NOTIFICATION       = "VENDOR_VERIFICATION"
CUSTOMER_PASSWORD_RESET_LINK           = "CUSTOMER_PASSWORD_RESET_LINK"
VENDOR_PASSWORD_RESET_OTP              = "VENDOR_PASSWORD_RESET_OTP"
ADMIN_LOGIN_OTP_NOTIFICATION           = "ADMIN_LOGIN_OTP"
ADMIN_PASSWORD_RESET_OTP               = "ADMIN_PASSWORD_RESET_OTP"

# ── Statuses / channels ───────────────────────────────────────────────────────
NOTIFICATION_CHANNEL_EMAIL             = "EMAIL"
NOTIFICATION_STATUS_QUEUED             = "QUEUED"
NOTIFICATION_STATUS_RETRY_PENDING      = "RETRY_PENDING"
NOTIFICATION_STATUS_PROCESSING         = "PROCESSING"
NOTIFICATION_STATUS_SENT               = "SENT"
NOTIFICATION_STATUS_PERMANENT_FAILURE  = "PERMANENT_FAILURE"

DEFAULT_IDEMPOTENCY_WINDOW = timedelta(minutes=10)
DEFAULT_MAX_ATTEMPTS       = 4
DEFAULT_RETRY_DELAY        = timedelta(minutes=1)


@dataclass(frozen=True)
class NotificationTemplate:
    subject: str
    text_body: str
    html_body: str


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    provider: str
    provider_message_id: str | None = None
    error_message: str | None = None


# ── Shared OTP block helpers ──────────────────────────────────────────────────
def _otp_text(otp: str, expiry_minutes: int = 5) -> str:
    return (
        f"    {otp}\n\n"
        f"This code expires in {expiry_minutes} minutes.\n\n"
        "Do not share this code with anyone."
    )


def _otp_html_block(otp: str, expiry_minutes: int = 5) -> str:
    return (
        f"<p style='font-size:36px;font-weight:bold;letter-spacing:10px;"
        f"color:#6C3FC5;margin:24px 0;text-align:center;'>{otp}</p>"
        f"<p style='color:#888;font-size:13px;text-align:center;'>"
        f"Expires in {expiry_minutes} minutes &nbsp;|&nbsp; Do not share this code.</p>"
    )


# ── Email templates ───────────────────────────────────────────────────────────
_TEMPLATES: dict[str, NotificationTemplate] = {

    CUSTOMER_VERIFICATION_NOTIFICATION: NotificationTemplate(
        subject="Verify your Occacia account",
        text_body=(
            "Welcome to Occacia, {userName}!\n\n"
            "Please verify your email address to activate your account:\n\n"
            "{verificationLink}\n\n"
            "This link expires in 24 hours.\n"
            "If you did not create an account, you can safely ignore this email."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#6C3FC5;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Welcome, {userName}!</h2>"
            "<p>Thank you for creating a customer account. Please verify your email "
            "address to activate your account and start planning your events.</p>"
            "<div style='text-align:center;margin:32px 0;'>"
            "<a href='{verificationLink}' style='background:#6C3FC5;color:#fff;"
            "padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;"
            "font-size:16px;'>Verify My Account</a></div>"
            "<p style='color:#888;font-size:13px;'>This link expires in 24 hours.<br>"
            "If you did not create an account, you can safely ignore this email.</p>"
            "</div></body></html>"
        ),
    ),

    VENDOR_VERIFICATION_NOTIFICATION: NotificationTemplate(
        subject="Verify your Occacia vendor account",
        text_body=(
            "Welcome to Occacia Vendors, {userName}!\n\n"
            "Please verify your email address to complete your vendor registration:\n\n"
            "{verificationLink}\n\n"
            "After verification your account will be reviewed by our team.\n"
            "This link expires in 24 hours."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#6C3FC5;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia Vendors</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Welcome, {userName}!</h2>"
            "<p>Thank you for registering as a vendor. Please verify your email address "
            "to complete your registration.</p>"
            "<div style='text-align:center;margin:32px 0;'>"
            "<a href='{verificationLink}' style='background:#6C3FC5;color:#fff;"
            "padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;"
            "font-size:16px;'>Verify Vendor Account</a></div>"
            "<p>After verification, your account will be reviewed by our team. "
            "You will receive an email once approved.</p>"
            "<p style='color:#888;font-size:13px;'>This link expires in 24 hours.</p>"
            "</div></body></html>"
        ),
    ),

    CUSTOMER_PASSWORD_RESET_LINK: NotificationTemplate(
        subject="Reset your Occacia password",
        text_body=(
            "Hi {userName},\n\n"
            "We received a request to reset the password for your Occacia customer account.\n\n"
            "Use the secure password reset link below to continue:\n\n"
            "{resetLink}\n\n"
            "This link expires in 10 minutes and can only be used once.\n\n"
            "If you did not request a password reset, you can safely ignore this email."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#6C3FC5;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Reset Your Password</h2>"
            "<p>Hi {userName},</p>"
            "<p>We received a request to reset the password for your Occacia customer account. "
            "Use the secure link below to set a new password:</p>"
            "<div style='text-align:center;margin:32px 0;'>"
            "<a href='{resetLink}' style='background:#6C3FC5;color:#fff;"
            "padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;"
            "font-size:16px;'>Reset My Password</a></div>"
            "<p style='color:#888;font-size:13px;'>This link expires in 10 minutes and can only be used once.</p>"
            "<p style='color:#888;font-size:13px;'>"
            "If you did not request this, your password will not be changed.</p>"
            "</div></body></html>"
        ),
    ),

    VENDOR_PASSWORD_RESET_OTP: NotificationTemplate(
        subject="Your Occacia vendor account password reset code",
        text_body=(
            "Hi {userName},\n\n"
            "We received a request to reset the password for your Occacia vendor account.\n\n"
            "Your password reset code is:\n\n"
            "{otpCode}\n\n"
            "Enter this code on the password reset page to continue.\n\n"
            "If you did not request a password reset, you can safely ignore this email."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#6C3FC5;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia Vendors</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Vendor Password Reset Code</h2>"
            "<p>Hi {userName},</p>"
            "<p>We received a request to reset the password for your Occacia vendor account. "
            "Enter the code below on the password reset page:</p>"
            "{otpBlock}"
            "<p style='color:#888;font-size:13px;'>"
            "If you did not request this, your password will not be changed.</p>"
            "</div></body></html>"
        ),
    ),

    ADMIN_LOGIN_OTP_NOTIFICATION: NotificationTemplate(
        subject="Your Occacia Admin Login Code",
        text_body=(
            "Hi {userName},\n\n"
            "Your one-time login code for Occacia Admin is:\n\n"
            "{otpCode}\n\n"
            "This code expires in 5 minutes.\n"
            "If you did not attempt to log in, contact your system administrator immediately."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#1a1a2e;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia Admin</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Admin Login Verification</h2>"
            "<p>Hi {userName},</p>"
            "<p>Your one-time login code for Occacia Admin is:</p>"
            "{otpBlock}"
            "<p style='color:#888;font-size:13px;'>"
            "If you did not attempt to log in, please contact your system administrator immediately.</p>"
            "</div></body></html>"
        ),
    ),

    ADMIN_PASSWORD_RESET_OTP: NotificationTemplate(
        subject="Your Occacia Admin Password Reset Code",
        text_body=(
            "Hi {userName},\n\n"
            "We received a request to reset the password for your Occacia Admin account.\n\n"
            "Your password reset code is:\n\n"
            "{otpCode}\n\n"
            "This code expires in 5 minutes.\n"
            "If you did not request this, contact your system administrator immediately."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#1a1a2e;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia Admin</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Admin Password Reset Code</h2>"
            "<p>Hi {userName},</p>"
            "<p>We received a request to reset your Occacia Admin account password. "
            "Enter the code below to continue:</p>"
            "{otpBlock}"
            "<p style='color:#888;font-size:13px;'>"
            "If you did not request this, contact your system administrator immediately.</p>"
            "</div></body></html>"
        ),
    ),

    TASK_CONFIRMED_NOTIFICATION: NotificationTemplate(
        subject="Task confirmed for {eventTitle}",
        text_body=(
            "Hi {userName},\n\n"
            "Your task has been confirmed in Occacia.\n\n"
            "Event: {eventTitle}\n"
            "Task: {taskTitle}\n"
            "Task ID: {taskId}\n\n"
            "We will keep you updated as planning progresses."
        ),
        html_body=(
            "<html><body style='font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;'>"
            "<div style='background:#6C3FC5;padding:24px;text-align:center;'>"
            "<h1 style='color:#fff;margin:0;font-size:24px;'>Occacia</h1></div>"
            "<div style='padding:32px;'>"
            "<h2 style='color:#6C3FC5;'>Task Confirmed</h2>"
            "<p>Hi {userName}, your task has been confirmed.</p>"
            "<table style='border-collapse:collapse;width:100%;margin:16px 0;'>"
            "<tr style='background:#f5f0ff;'><td style='padding:10px;font-weight:bold;'>Event</td>"
            "<td style='padding:10px;'>{eventTitle}</td></tr>"
            "<tr><td style='padding:10px;font-weight:bold;'>Task</td>"
            "<td style='padding:10px;'>{taskTitle}</td></tr>"
            "<tr style='background:#f5f0ff;'><td style='padding:10px;font-weight:bold;'>Task ID</td>"
            "<td style='padding:10px;'>{taskId}</td></tr>"
            "</table>"
            "</div></body></html>"
        ),
    ),
}


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


class NotificationService:

    # ── Core enqueue ──────────────────────────────────────────────────────────

    def enqueue_notification(
        self,
        db: Session,
        *,
        notification_type: str,
        recipient_id: str,
        context_data: dict[str, object],
        dedupe_window: timedelta | None = None,
    ) -> Notification | None:
        recipient  = self._resolve_recipient(db, recipient_id=recipient_id)
        dedupe_key = self._build_dedupe_key(
            notification_type=notification_type,
            recipient_id=recipient_id,
            context_data=context_data,
        )

        if dedupe_key and dedupe_window and self._has_recent_non_terminal(
            db, type=notification_type, dedupe_key=dedupe_key, window=dedupe_window,
        ):
            logger.info("Skipping duplicate %s for %s", notification_type, recipient_id)
            return None

        rendered  = self.render_template(
            notification_type=notification_type,
            recipient_name=recipient["name"],
            context_data=context_data,
        )
        timestamp = now_utc()
        notification = Notification(
            user_id=recipient_id,
            recipient_email=recipient["email"],
            recipient_name=recipient["name"],
            event_id=self._string_or_none(context_data.get("eventId")),
            task_id=self._string_or_none(context_data.get("taskId")),
            channel=NOTIFICATION_CHANNEL_EMAIL,
            type=notification_type,
            status=NOTIFICATION_STATUS_QUEUED,
            dedupe_key=dedupe_key,
            payload=context_data,
            subject=rendered.subject,
            body_text=rendered.text_body,
            body_html=rendered.html_body,
            provider="SMTP",
            attempt_count=0,
            max_attempts=DEFAULT_MAX_ATTEMPTS,
            next_attempt_at=timestamp,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def render_template(
        self,
        *,
        notification_type: str,
        recipient_name: str,
        context_data: dict[str, object],
    ) -> NotificationTemplate:
        template  = _TEMPLATES[notification_type]
        text_ctx  = self._build_template_context(
            recipient_name=recipient_name, context_data=context_data, html_escape=False,
        )
        html_ctx  = self._build_template_context(
            recipient_name=recipient_name, context_data=context_data, html_escape=True,
        )

        # Inject OTP HTML block for templates that use {otpBlock}
        otp_code = str(context_data.get("otpCode", ""))
        html_ctx["otpBlock"] = _otp_html_block(otp_code) if otp_code else ""

        return NotificationTemplate(
            subject=template.subject.format_map(_SafeDict(text_ctx)),
            text_body=template.text_body.format_map(_SafeDict(text_ctx)),
            html_body=template.html_body.format_map(_SafeDict(html_ctx)),
        )

    # ── Worker ────────────────────────────────────────────────────────────────

    def process_pending_notifications(self, db: Session, *, batch_size: int = 20) -> int:
        now   = now_utc()
        items = (
            db.query(Notification)
            .filter(
                Notification.channel == NOTIFICATION_CHANNEL_EMAIL,
                Notification.status.in_([
                    NOTIFICATION_STATUS_QUEUED,
                    NOTIFICATION_STATUS_RETRY_PENDING,
                ]),
                Notification.next_attempt_at.is_not(None),
                Notification.next_attempt_at <= now,
            )
            .order_by(Notification.next_attempt_at.asc(), Notification.id.asc())
            .limit(batch_size)
            .all()
        )
        for notification in items:
            self._deliver_notification(db, notification=notification)
        return len(items)

    # ── Queue helpers — Customer ──────────────────────────────────────────────

    def queue_customer_verification(
        self, db: Session, *, customer: Customer, verification_token: str,
    ) -> Notification | None:
        return self.enqueue_notification(
            db,
            notification_type=CUSTOMER_VERIFICATION_NOTIFICATION,
            recipient_id=customer.customer_id,
            context_data={
                "userId": customer.customer_id,
                "userName": customer.full_name,
                "userEmail": customer.email,
                "verificationToken": verification_token,
                "verificationLink": (
                    f"https://app.occacia.com/customer/auth/verify-email"
                    f"?token={verification_token}"
                ),
            },
        )

    def queue_customer_password_reset_link(
        self, db: Session, *, customer: Customer, reset_token: str,
    ) -> Notification | None:
        return self.enqueue_notification(
            db,
            notification_type=CUSTOMER_PASSWORD_RESET_LINK,
            recipient_id=customer.customer_id,
            context_data={
                "userId": customer.customer_id,
                "userName": customer.full_name,
                "userEmail": customer.email,
                "resetToken": reset_token,
                "resetLink": (
                    f"https://app.occacia.com/customer/auth/reset-password"
                    f"?token={reset_token}"
                ),
            },
        )

    # ── Queue helpers — Vendor ────────────────────────────────────────────────

    def queue_vendor_verification(
        self, db: Session, *, vendor: Vendor, verification_token: str,
    ) -> Notification | None:
        return self.enqueue_notification(
            db,
            notification_type=VENDOR_VERIFICATION_NOTIFICATION,
            recipient_id=vendor.vendor_id,
            context_data={
                "userId": vendor.vendor_id,
                "userName": vendor.display_name or vendor.business_name or vendor.email,
                "userEmail": vendor.email,
                "verificationToken": verification_token,
                "verificationLink": (
                    f"https://app.occacia.com/vendor/auth/verify-email"
                    f"?token={verification_token}"
                ),
            },
        )

    def queue_vendor_password_reset_otp(
        self, db: Session, *, vendor: Vendor, otp_code: str,
    ) -> Notification | None:
        return self.enqueue_notification(
            db,
            notification_type=VENDOR_PASSWORD_RESET_OTP,
            recipient_id=vendor.vendor_id,
            context_data={
                "userId": vendor.vendor_id,
                "userName": vendor.display_name or vendor.business_name or vendor.email,
                "userEmail": vendor.email,
                "otpCode": otp_code,
            },
        )

    # ── Queue helpers — Admin ─────────────────────────────────────────────────

    def queue_admin_login_otp(
        self, db: Session, *, admin: Admin, otp_code: str,
    ) -> Notification | None:
        return self.enqueue_notification(
            db,
            notification_type=ADMIN_LOGIN_OTP_NOTIFICATION,
            recipient_id=admin.admin_id,
            context_data={
                "userId": admin.admin_id,
                "userName": admin.email,
                "userEmail": admin.email,
                "otpCode": otp_code,
            },
        )

    def queue_admin_password_reset_otp(
        self, db: Session, *, admin: Admin, otp_code: str,
    ) -> Notification | None:
        return self.enqueue_notification(
            db,
            notification_type=ADMIN_PASSWORD_RESET_OTP,
            recipient_id=admin.admin_id,
            context_data={
                "userId": admin.admin_id,
                "userName": admin.email,
                "userEmail": admin.email,
                "otpCode": otp_code,
            },
        )

    # ── Queue helpers — Tasks ─────────────────────────────────────────────────

    def send_task_confirmed_notifications(
        self,
        db: Session,
        *,
        customer: Customer,
        event: Event,
        tasks: list[Task],
        window: timedelta = DEFAULT_IDEMPOTENCY_WINDOW,
    ) -> list[Notification]:
        notifications: list[Notification] = []
        for task in tasks:
            n = self.enqueue_notification(
                db,
                notification_type=TASK_CONFIRMED_NOTIFICATION,
                recipient_id=customer.customer_id,
                context_data={
                    "userId": customer.customer_id,
                    "userName": customer.full_name,
                    "userEmail": customer.email,
                    "eventId": event.event_id,
                    "eventTitle": event.title,
                    "taskId": task.task_id,
                    "taskTitle": task.name,
                    "taskStatus": task.status,
                    "confirmedAt": task.confirmed_at.isoformat() if task.confirmed_at else None,
                },
                dedupe_window=window,
            )
            if n is not None:
                notifications.append(n)
        return notifications

    # ── Notification listing ──────────────────────────────────────────────────

    def list_notifications(
        self,
        db: Session,
        *,
        limit: int,
        cursor: str | None,
        user_id: str | None = None,
        event_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        type: str | None = None,
    ) -> tuple[list[Notification], str | None]:
        query = db.query(Notification)
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        if event_id:
            query = query.filter(Notification.event_id == event_id)
        if task_id:
            query = query.filter(Notification.task_id == task_id)
        if status:
            query = query.filter(Notification.status == status.upper())
        if type:
            query = query.filter(Notification.type == type.upper())
        if cursor:
            row = db.query(Notification).filter(Notification.notification_id == cursor).first()
            if row:
                query = query.filter(
                    or_(
                        Notification.created_at < row.created_at,
                        and_(
                            Notification.created_at == row.created_at,
                            Notification.id > row.id,
                        ),
                    )
                )
        items = (
            query.order_by(Notification.created_at.desc(), Notification.id.asc())
            .limit(limit + 1)
            .all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].notification_id
            items = items[:limit]
        return items, next_cursor

    # ── Delivery ──────────────────────────────────────────────────────────────

    def _deliver_notification(self, db: Session, *, notification: Notification) -> Notification:
        notification.status         = NOTIFICATION_STATUS_PROCESSING
        notification.last_attempt_at = now_utc()
        db.add(notification)
        db.commit()
        db.refresh(notification)

        result = self._send_email(
            to=notification.recipient_email,
            subject=notification.subject,
            text_body=notification.body_text,
            html_body=notification.body_html,
        )

        notification.attempt_count        = (notification.attempt_count or 0) + 1
        notification.provider             = result.provider
        notification.provider_message_id  = result.provider_message_id
        notification.error_message        = result.error_message

        if result.success:
            notification.status           = NOTIFICATION_STATUS_SENT
            notification.sent_at          = now_utc()
            notification.next_attempt_at  = None
        else:
            if notification.attempt_count >= (notification.max_attempts or DEFAULT_MAX_ATTEMPTS):
                notification.status          = NOTIFICATION_STATUS_PERMANENT_FAILURE
                notification.next_attempt_at = None
            else:
                notification.status          = NOTIFICATION_STATUS_RETRY_PENDING
                notification.next_attempt_at = now_utc() + DEFAULT_RETRY_DELAY

        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def _send_email(
        self,
        *,
        to: str,
        subject: str,
        text_body: str,
        html_body: str | None,
    ) -> ProviderResult:
        smtp_host     = settings.SMTP_HOST
        smtp_port     = settings.SMTP_PORT
        smtp_user     = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        from_email    = settings.FROM_EMAIL
        smtp_use_tls  = settings.SMTP_USE_TLS

        if not smtp_host:
            logger.warning("SMTP_HOST not set — email not sent (dev mode)")
            logger.info("DEV EMAIL\n  To: %s\n  Subject: %s\n  Body:\n%s", to, subject, text_body)
            return ProviderResult(success=False, provider="SMTP", error_message="SMTP_HOST not configured")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Occacia <{from_email}>"
        msg["To"]      = to
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, [to], msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    server.ehlo()
                    if smtp_use_tls:
                        server.starttls()
                        server.ehlo()
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, [to], msg.as_string())

            logger.info("Email sent via SMTP to %s | Subject: %s", to, subject)
            return ProviderResult(success=True, provider="SMTP")

        except smtplib.SMTPAuthenticationError as exc:
            logger.error("SMTP auth failed: %s", exc)
            return ProviderResult(success=False, provider="SMTP", error_message=f"Auth failed: {exc}")
        except smtplib.SMTPRecipientsRefused as exc:
            logger.error("SMTP recipient refused %s: %s", to, exc)
            return ProviderResult(success=False, provider="SMTP", error_message=f"Recipient refused: {exc}")
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to, exc)
            return ProviderResult(success=False, provider="SMTP", error_message=str(exc))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _resolve_recipient(self, db: Session, *, recipient_id: str) -> dict[str, str]:
        if recipient_id.startswith("CUS"):
            c = db.query(Customer).filter(Customer.customer_id == recipient_id).first()
            if c:
                return {"email": c.email, "name": c.full_name or c.email}
        if recipient_id.startswith("VEN"):
            v = db.query(Vendor).filter(Vendor.vendor_id == recipient_id).first()
            if v:
                return {"email": v.email, "name": v.display_name or v.business_name or v.email}
        if recipient_id.startswith("ADM"):
            a = db.query(Admin).filter(Admin.admin_id == recipient_id).first()
            if a:
                return {"email": a.email, "name": a.email}
        if recipient_id.startswith("USR"):
            u = db.query(User).filter(User.user_id == recipient_id).first()
            if u:
                return {"email": u.email, "name": u.email}
        # fallback
        c = db.query(Customer).filter(Customer.customer_id == recipient_id).first()
        if c:
            return {"email": c.email, "name": c.full_name or c.email}
        v = db.query(Vendor).filter(Vendor.vendor_id == recipient_id).first()
        if v:
            return {"email": v.email, "name": v.display_name or v.business_name or v.email}
        raise ValueError(f"Unsupported recipient_id: {recipient_id}")

    def _has_recent_non_terminal(
        self, db: Session, *, type: str, dedupe_key: str, window: timedelta,
    ) -> bool:
        cutoff = now_utc() - window
        return (
            db.query(Notification)
            .filter(
                Notification.type == type,
                Notification.dedupe_key == dedupe_key,
                Notification.created_at >= cutoff,
                Notification.status.in_([
                    NOTIFICATION_STATUS_QUEUED,
                    NOTIFICATION_STATUS_PROCESSING,
                    NOTIFICATION_STATUS_RETRY_PENDING,
                    NOTIFICATION_STATUS_SENT,
                ]),
            )
            .first()
        ) is not None

    def _build_dedupe_key(
        self,
        *,
        notification_type: str,
        recipient_id: str,
        context_data: dict[str, object],
    ) -> str | None:
        if notification_type == TASK_CONFIRMED_NOTIFICATION:
            event_id = self._string_or_none(context_data.get("eventId"))
            task_id  = self._string_or_none(context_data.get("taskId"))
            if event_id and task_id:
                return f"{notification_type}:{recipient_id}:{event_id}:{task_id}"
        return None

    def _build_template_context(
        self,
        *,
        recipient_name: str,
        context_data: dict[str, object],
        html_escape: bool,
    ) -> dict[str, str]:
        context = {"userName": recipient_name}
        formatter = Formatter()
        for key, value in context_data.items():
            normalized = "" if value is None else str(value)
            context[key] = html.escape(normalized) if html_escape else normalized
        all_text = " ".join([t.subject + t.text_body + t.html_body for t in _TEMPLATES.values()])
        for _, field_name, _, _ in formatter.parse(all_text):
            if field_name and field_name not in context:
                context[field_name] = ""
        return context

    @staticmethod
    def _string_or_none(value: object | None) -> str | None:
        return None if value is None else str(value)


notification_service = NotificationService()
