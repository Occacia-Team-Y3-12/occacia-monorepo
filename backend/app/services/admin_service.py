"""
app/services/admin_service.py
"""
from __future__ import annotations

import logging
import os
import random
import string
from datetime import UTC, datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.enums import TaskStatus
from app.common.utils import now_utc
from app.core.config import settings
from app.core.security import (
    ALGORITHM, SECRET_KEY,
    create_refresh_token,
    decode_token,
    get_password_hash, verify_password,
)
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.offering import Offering
from app.models.package_execution_request import PackageExecutionRequest
from app.models.support_note import SupportNote
from app.models.task import Task
from app.models.task_recommendation import TaskRecommendation
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)

ADMIN_TOKEN_EXPIRE_MINUTES = 120
OTP_TTL_SECONDS            = 300   # 5 minutes
OTP_LENGTH                 = 6
RESET_TOKEN_TTL_MINUTES    = 10
EMAIL_VERIFICATION_TTL_HOURS = 24

_TERMINAL_TASK_STATUSES    = {"DONE"}
_ACTIVE_TASK_STATUSES      = {"PENDING", "ASSIGNED", "IN_PROGRESS"}
_OVERRIDABLE_TASK_STATUSES = {s.value for s in TaskStatus}


# ── Redis helper ──────────────────────────────────────────────────────────────

def _get_redis():
    try:
        import redis as redis_lib
        client = redis_lib.from_url(
            getattr(settings, "REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
            socket_connect_timeout=3,
        )
        client.ping()
        return client
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        return None


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


class AdminService:

    # ── JWT helpers ───────────────────────────────────────────────────────────

    def _create_admin_token(self, admin_id: str, staff_role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_EXPIRE_MINUTES)
        return jwt.encode(
            {"sub": admin_id, "type": "admin", "role": staff_role, "exp": expire},
            SECRET_KEY, algorithm=ALGORITHM,
        )

    def _create_reset_token(self, email: str) -> str:
        expires_at = datetime.now(UTC) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
        return jwt.encode(
            {"sub": email, "type": "admin_pwd_reset_verified", "exp": expires_at},
            SECRET_KEY, algorithm=ALGORITHM,
        )

    def _decode_reset_token(self, token: str) -> dict:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new OTP.") from exc
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=400, detail="Invalid reset token.") from exc
        if claims.get("type") != "admin_pwd_reset_verified":
            raise HTTPException(status_code=400, detail="Invalid reset token.")
        return claims

    def _create_verification_token(self, email: str) -> tuple[str, datetime]:
        expires_at = datetime.now(UTC) + timedelta(hours=EMAIL_VERIFICATION_TTL_HOURS)
        token = jwt.encode(
            {"sub": email, "type": "verify_admin_email", "exp": expires_at},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        return token, expires_at

    def _decode_verification_token(self, token: str) -> dict:
        try:
            claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=400, detail="Verification token has expired.") from exc
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=400, detail="Invalid verification token.") from exc
        if claims.get("type") != "verify_admin_email":
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        return claims

    # ── Registration ──────────────────────────────────────────────────────────

    def register_admin(
        self, db: Session, email: str, password: str, staff_role: str = None,
    ) -> Admin:
        if db.query(Admin).filter(Admin.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered.")
        verification_token, expires_at = self._create_verification_token(email)
        admin = Admin(
            email=email,
            password_hash=get_password_hash(password),
            staff_role=staff_role or "staff",
            email_verified=False,
            status="PENDING",
            verification_token=verification_token,
            verification_token_expires_at=expires_at,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        try:
            from app.services.notification_service import notification_service
            notification_service.queue_admin_verification(
                db, admin=admin, verification_token=verification_token,
            )
        except Exception as exc:
            logger.error("Failed to queue admin verification email: %s", exc)
        logger.info("New admin created: %s (%s)", admin.email, admin.staff_role)
        return admin

    def verify_admin_email(self, db: Session, token: str) -> dict[str, str]:
        claims = self._decode_verification_token(token)
        email = claims.get("sub")
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        if admin.email_verified:
            return {"message": "Email already verified"}
        if admin.verification_token != token:
            raise HTTPException(status_code=400, detail="Invalid verification token.")
        admin.email_verified = True
        admin.status = "ACTIVE"
        admin.verification_token = None
        admin.verification_token_expires_at = None
        db.add(admin)
        db.commit()
        return {"message": "Email verified successfully"}

    def resend_admin_verification_email(self, db: Session, email: str) -> dict[str, str]:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=400, detail="Admin account not found.")
        if admin.email_verified or getattr(admin, "status", None) == "ACTIVE":
            raise HTTPException(status_code=400, detail="Email already verified.")
        verification_token, expires_at = self._create_verification_token(email)
        admin.verification_token = verification_token
        admin.verification_token_expires_at = expires_at
        db.add(admin)
        db.commit()
        db.refresh(admin)
        try:
            from app.services.notification_service import notification_service
            notification_service.queue_admin_verification(
                db, admin=admin, verification_token=verification_token,
            )
        except Exception as exc:
            logger.error("Failed to queue admin verification email: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to send verification email.")
        return {"message": "Verification email resent successfully."}

    # ── Login — Step 1: validate password → send OTP ──────────────────────────

    def login_admin(self, db: Session, email: str, password: str) -> dict:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin or not verify_password(password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password.")
        if os.getenv("SKIP_EMAIL_VERIFICATION") != "true" and not admin.email_verified:
            raise HTTPException(status_code=403, detail="Email not verified.")
        status_value = getattr(admin, "status", "ACTIVE")
        if status_value and status_value != "ACTIVE":
            raise HTTPException(status_code=403, detail="Admin account is not active.")

        otp_code  = _generate_otp()
        redis     = _get_redis()
        redis_key = f"admin_otp:{admin.admin_id}"
        if redis:
            redis.setex(redis_key, OTP_TTL_SECONDS, otp_code)
        else:
            logger.warning("Redis unavailable — admin login OTP for %s: %s", admin.email, otp_code)

        try:
            from app.services.notification_service import notification_service
            notification_service.queue_admin_login_otp(db, admin=admin, otp_code=otp_code)
        except Exception as exc:
            logger.error("Failed to queue admin login OTP: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to send OTP email. Please try again.")

        return {
            "message": "A one-time login code has been sent to your email address.",
            "email": admin.email,
        }

    # ── Login — Step 2: verify OTP → return JWT ───────────────────────────────

    def verify_admin_login_otp(self, db: Session, email: str, otp_code: str) -> dict:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        redis     = _get_redis()
        redis_key = f"admin_otp:{admin.admin_id}"
        if not redis:
            raise HTTPException(status_code=503, detail="OTP verification service temporarily unavailable.")

        stored = redis.get(redis_key)
        if not stored:
            raise HTTPException(
                status_code=400,
                detail="OTP has expired or was never issued. Please request a new one.",
            )
        if stored != otp_code.strip():
            raise HTTPException(status_code=400, detail="Invalid OTP code.")
        redis.delete(redis_key)  # one-time use

        token = self._create_admin_token(admin.admin_id, admin.staff_role or "staff")
        refresh_token = create_refresh_token(
            data={"sub": admin.admin_id, "role": "ADMIN", "staffRole": admin.staff_role or "staff"},
            expires_delta=timedelta(days=7),
        )
        logger.info("Admin login verified for: %s", admin.email)
        return {
            "access_token": token,
            "accessToken": token,
            "refreshToken": refresh_token,
            "token_type": "bearer",
            "role": admin.staff_role,
            "user": {
                "userId": admin.admin_id,
                "email": admin.email,
                "role": admin.staff_role,
            },
        }

    def refresh_admin_token(self, db: Session, refresh_token: str) -> dict:
        exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
        try:
            claims = decode_token(refresh_token)
        except jwt.PyJWTError:
            raise exc
        if claims.get("type") != "refresh" or claims.get("role") != "ADMIN":
            raise exc
        admin_id = claims.get("sub")
        if not admin_id:
            raise exc
        admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
        if not admin:
            raise exc

        new_access_token = self._create_admin_token(admin.admin_id, admin.staff_role or "staff")
        new_refresh_token = create_refresh_token(
            data={"sub": admin.admin_id, "role": "ADMIN", "staffRole": admin.staff_role or "staff"},
            expires_delta=timedelta(days=7),
        )
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token,
            "user": {
                "userId": admin.admin_id,
                "email": admin.email,
                "role": "ADMIN",
                "status": getattr(admin, "status", "ACTIVE"),
            },
        }

    def logout_admin(self, db: Session, authorization: str | None) -> dict[str, str]:
        """Invalidate admin session token by adding it to blacklist (best effort)."""
        _ = db
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
            self._blacklist_token(token, role="ADMIN")
        return {"message": "Logged out successfully."}

    def delete_admin_account(
        self,
        db: Session,
        admin: Admin,
        authorization: str | None = None,
    ) -> dict[str, str]:
        """Delete authenticated admin account."""
        try:
            db.delete(admin)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Admin account cannot be deleted because related records exist.",
            )
        except Exception:
            db.rollback()
            raise

        if authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:]
            self._blacklist_token(token, role="ADMIN")
        return {"message": "Admin account deleted successfully."}

    def _blacklist_token(self, token: str, role: str) -> None:
        """Store token in Redis blacklist using remaining JWT lifetime as TTL."""
        try:
            claims = decode_token(token)
            exp = claims.get("exp")
            if exp:
                ttl = int(exp - datetime.now(UTC).timestamp())
                if ttl > 0:
                    redis = _get_redis()
                    if redis:
                        redis.setex(f"blacklist:{token}", ttl, role)
        except Exception as exc:
            logger.warning("Admin token blacklist failed (non-blocking): %s", exc)

    # ── Forgot password — Step 1: send OTP ───────────────────────────────────

    def request_admin_password_reset_otp(self, db: Session, email: str) -> dict:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            return {"message": "If this email is registered, a reset code has been sent."}

        otp_code  = _generate_otp()
        redis     = _get_redis()
        redis_key = f"pwd_otp:admin:{email}"
        if redis:
            redis.setex(redis_key, OTP_TTL_SECONDS, otp_code)
        else:
            logger.warning("Redis unavailable — admin pwd OTP for %s: %s", email, otp_code)

        try:
            from app.services.notification_service import notification_service
            notification_service.queue_admin_password_reset_otp(db, admin=admin, otp_code=otp_code)
        except Exception as exc:
            logger.error("Failed to queue admin password reset OTP: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to send OTP email. Please try again.")

        return {"message": "If this email is registered, a reset code has been sent."}

    # ── Forgot password — Step 2: verify OTP → return reset token ────────────

    def verify_admin_password_reset_otp(
        self, db: Session, email: str, otp_code: str,
    ) -> dict:
        redis     = _get_redis()
        redis_key = f"pwd_otp:admin:{email}"
        if not redis:
            raise HTTPException(status_code=503, detail="OTP service temporarily unavailable.")
        stored = redis.get(redis_key)
        if not stored:
            raise HTTPException(status_code=400, detail="OTP has expired or is invalid. Please request a new one.")
        if stored != otp_code.strip():
            raise HTTPException(status_code=400, detail="Invalid OTP code.")
        redis.delete(redis_key)

        reset_token = self._create_reset_token(email)
        return {"resetToken": reset_token, "message": "OTP verified. You may now reset your password."}

    # ── Forgot password — Step 3: reset password ─────────────────────────────

    def confirm_admin_password_reset(
        self, db: Session, reset_token: str, new_password: str,
    ) -> dict:
        claims = self._decode_reset_token(reset_token)
        email  = claims.get("sub")
        admin  = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found.")
        admin.password_hash = get_password_hash(new_password)
        db.add(admin)
        db.commit()
        logger.info("Admin password reset for: %s", email)
        return {"message": "Password updated successfully."}

    # ── Vendor management ─────────────────────────────────────────────────────

    def get_vendor(self, db: Session, vendor_id: int) -> Vendor:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")
        return vendor

    def list_vendors(
        self, db: Session,
        approval_status: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[Vendor]:
        query = db.query(Vendor)
        if approval_status:
            query = query.filter(Vendor.approval_status == approval_status.upper())
        if status:
            query = query.filter(Vendor.status == status.upper())
        return query.order_by(Vendor.id.desc()).all()

    def update_vendor_status(
        self, db: Session, vendor_id: int, new_status: str, admin_email: str,
    ) -> Vendor:
        if not new_status or new_status.upper() not in ("ACTIVE", "SUSPENDED", "DISABLED"):
            raise HTTPException(status_code=400, detail="status must be ACTIVE, SUSPENDED, or DISABLED")
        vendor = self.get_vendor(db, vendor_id)
        if hasattr(vendor, "status"):
            vendor.status = new_status.upper()
        db.commit()
        db.refresh(vendor)
        logger.info("Admin %s set vendor %s status to %s", admin_email, vendor_id, new_status)
        return vendor

    def approve_vendor(self, db: Session, vendor_id: int, admin_email: str) -> Vendor:
        vendor = self.get_vendor(db, vendor_id)
        if vendor.approval_status == "APPROVED":
            raise HTTPException(status_code=400, detail="Vendor is already approved.")
        vendor.is_verified     = True
        vendor.approval_status = "APPROVED"
        vendor.approved_at     = datetime.now(timezone.utc)
        if hasattr(vendor, "status"):
            vendor.status = "ACTIVE"
        db.commit()
        db.refresh(vendor)
        logger.info("Admin %s approved vendor %s", admin_email, vendor.vendor_id)
        return vendor

    def reject_vendor(
        self, db: Session, vendor_id: int, reason: str, admin_email: str,
    ) -> Vendor:
        vendor = self.get_vendor(db, vendor_id)
        if vendor.approval_status == "REJECTED":
            raise HTTPException(status_code=400, detail="Vendor is already rejected.")
        vendor.is_verified     = False
        vendor.approval_status = "REJECTED"
        db.commit()
        db.refresh(vendor)
        logger.info("Admin %s rejected vendor %s", admin_email, vendor.vendor_id)
        return vendor

    # ── Customer management ───────────────────────────────────────────────────

    def list_customers(
        self, db: Session,
        status: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> tuple[list[Customer], Optional[str]]:
        query = db.query(Customer)
        if status:
            query = query.filter(Customer.status == status.upper())
        if cursor:
            c = db.query(Customer).filter(Customer.customer_id == cursor).first()
            if c:
                query = query.filter(Customer.id < c.id)
        customers = query.order_by(Customer.id.desc()).limit(limit + 1).all()
        next_cursor = None
        if len(customers) > limit:
            next_cursor = customers[limit - 1].customer_id
            customers   = customers[:limit]
        return customers, next_cursor

    def get_customer(self, db: Session, customer_id: str) -> Customer:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found.")
        return customer

    def update_customer_status(
        self, db: Session, customer_id: str, new_status: str, admin_email: str,
    ) -> Customer:
        if not new_status or new_status.upper() not in ("ACTIVE", "SUSPENDED", "DISABLED", "PENDING"):
            raise HTTPException(status_code=400, detail="status must be ACTIVE, SUSPENDED, DISABLED, or PENDING")
        customer        = self.get_customer(db, customer_id)
        customer.status = new_status.upper()
        db.commit()
        db.refresh(customer)
        logger.info("Admin %s set customer %s status to %s", admin_email, customer_id, new_status)
        return customer

    # ── Internal notes ────────────────────────────────────────────────────────

    def list_internal_notes(
        self, db: Session, *, event_id, task_id, vendor_id, package_order_id, limit, cursor,
    ) -> tuple[list[SupportNote], str | None]:
        query = db.query(SupportNote)
        if event_id:
            query = query.filter(SupportNote.event_id == event_id)
        if task_id:
            query = query.filter(SupportNote.task_id == task_id)
        if vendor_id:
            query = query.filter(SupportNote.vendor_id == vendor_id)
        if package_order_id:
            query = query.filter(SupportNote.package_order_id == package_order_id)
        if cursor:
            row = db.query(SupportNote).filter(SupportNote.note_id == cursor).first()
            if row:
                query = query.filter(
                    or_(SupportNote.created_at < row.created_at,
                        and_(SupportNote.created_at == row.created_at, SupportNote.id > row.id))
                )
        items = (
            query.order_by(SupportNote.created_at.desc(), SupportNote.id.asc())
            .limit(limit + 1).all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].note_id
            items       = items[:limit]
        return items, next_cursor

    def create_internal_note(
        self, db: Session, *, admin_id, package_order_id, event_id, task_id, vendor_id, action_type, note,
    ) -> SupportNote:
        n = SupportNote(
            admin_id=admin_id, package_order_id=package_order_id,
            event_id=event_id, task_id=task_id, vendor_id=vendor_id,
            action_type=action_type, note=note.strip(),
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        return n

    # ── Package orders ────────────────────────────────────────────────────────

    def list_package_orders(
        self, db: Session, *, status_filter, event_id, limit, cursor,
    ) -> tuple[list[PackageExecutionRequest], str | None]:
        query = db.query(PackageExecutionRequest)
        if status_filter:
            query = query.filter(PackageExecutionRequest.status == status_filter.upper())
        if event_id:
            query = query.filter(PackageExecutionRequest.event_id == event_id)
        if cursor:
            row = db.query(PackageExecutionRequest).filter(
                PackageExecutionRequest.execution_request_id == cursor).first()
            if row:
                query = query.filter(
                    or_(PackageExecutionRequest.created_at < row.created_at,
                        and_(PackageExecutionRequest.created_at == row.created_at,
                             PackageExecutionRequest.id > row.id))
                )
        items = (
            query.order_by(PackageExecutionRequest.created_at.desc(), PackageExecutionRequest.id.asc())
            .limit(limit + 1).all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].execution_request_id
            items       = items[:limit]
        return items, next_cursor

    def get_package_order(self, db: Session, *, package_order_id: str) -> PackageExecutionRequest:
        order = db.query(PackageExecutionRequest).filter(
            PackageExecutionRequest.execution_request_id == package_order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Package order not found")
        return order

    def get_package_order_detail(
        self, db: Session, *, package_order_id: str,
    ) -> tuple[PackageExecutionRequest, list[Task]]:
        order    = self.get_package_order(db, package_order_id=package_order_id)
        requests = (db.query(TaskRequest).filter(TaskRequest.package_order_id == package_order_id)
                    .order_by(TaskRequest.requested_at.asc(), TaskRequest.id.asc()).all())
        tasks    = self._get_tasks_by_ids(db, task_ids=[r.task_id for r in requests])
        return order, tasks

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def list_tasks(
        self, db: Session, *, status_filter, event_id, vendor_id, limit, cursor,
    ) -> tuple[list[Task], str | None]:
        query = db.query(Task)
        if status_filter:
            query = query.filter(Task.status == status_filter.upper())
        if event_id:
            query = query.filter(Task.event_id == event_id)
        if vendor_id:
            query = query.filter(Task.assigned_vendor_id == vendor_id)
        if cursor:
            row = db.query(Task).filter(Task.task_id == cursor).first()
            if row:
                query = query.filter(
                    or_(Task.created_at < row.created_at,
                        and_(Task.created_at == row.created_at, Task.id > row.id))
                )
        items = (
            query.order_by(Task.created_at.desc(), Task.id.asc())
            .limit(limit + 1).all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].task_id
            items       = items[:limit]
        return items, next_cursor

    def get_task(self, db: Session, *, task_id: str) -> Task:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def get_task_fulfillment_requests(self, db: Session, *, task_id: str) -> list[TaskRequest]:
        self.get_task(db, task_id=task_id)
        return (db.query(TaskRequest).filter(TaskRequest.task_id == task_id)
                .order_by(TaskRequest.requested_at.asc(), TaskRequest.id.asc()).all())

    def apply_task_support_action(
        self, db: Session, *, admin_id, task_id, action,
        assigned_vendor_id=None, expires_at=None, status_value=None, note=None,
    ) -> Task:
        task      = self.get_task(db, task_id=task_id)
        timestamp = now_utc()
        try:
            if action == "UNASSIGN_VENDOR":
                self._unassign_vendor(db, task=task, timestamp=timestamp)
            elif action == "EXTEND_EXPIRY":
                self._extend_expiry(task=task, expires_at=expires_at, timestamp=timestamp)
            elif action == "OVERRIDE_STATUS":
                self._override_status(task=task, status_value=status_value, timestamp=timestamp)
            elif action == "UNLOCK_EDITING":
                self._unlock_editing(task=task, timestamp=timestamp)
            elif action == "REASSIGN_VENDOR":
                self._reassign_vendor(db, task=task, assigned_vendor_id=assigned_vendor_id, timestamp=timestamp)
            else:
                raise HTTPException(status_code=400, detail="Unsupported admin task action")
            if note:
                db.add(SupportNote(
                    admin_id=admin_id,
                    package_order_id=self._get_latest_package_order_id(db, task_id=task.task_id),
                    event_id=task.event_id, task_id=task.task_id,
                    vendor_id=task.assigned_vendor_id or assigned_vendor_id,
                    action_type=action, note=note,
                ))
            db.add(task)
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(task)
        return task

    def _unassign_vendor(self, db, *, task, timestamp):
        if not task.assigned_vendor_id:
            raise HTTPException(status_code=409, detail="Task has no assigned vendor to unassign")
        if task.status in _TERMINAL_TASK_STATUSES or task.status == "IN_PROGRESS":
            raise HTTPException(status_code=409, detail="Task cannot be unassigned in its current state")
        self._cancel_open_requests(db, task_id=task.task_id)
        task.assigned_vendor_id = None; task.selected_offering_id = None
        task.status = "PENDING"; task.rejected_at = None; task.rejection_reason = None
        task.expires_at = None; task.status_updated_at = timestamp

    def _extend_expiry(self, *, task, expires_at, timestamp):
        if expires_at is None:
            raise HTTPException(status_code=400, detail="expiresAt is required for EXTEND_EXPIRY")
        if expires_at <= timestamp:
            raise HTTPException(status_code=400, detail="expiresAt must be in the future")
        if task.status not in {"PENDING", "EXPIRED"}:
            raise HTTPException(status_code=409, detail="Task expiry can only be extended for pending or expired tasks")
        task.expires_at = expires_at; task.status = "PENDING"; task.status_updated_at = timestamp

    def _override_status(self, *, task, status_value, timestamp):
        ns = (status_value or "").upper()
        if ns not in _OVERRIDABLE_TASK_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid target status")
        if task.status in _TERMINAL_TASK_STATUSES and ns != task.status:
            raise HTTPException(status_code=409, detail="Terminal tasks cannot be overridden")
        if ns in {"ASSIGNED", "IN_PROGRESS"} and not task.assigned_vendor_id:
            raise HTTPException(status_code=409, detail="Assigned vendor is required for the target status")
        task.status = ns
        if ns != "REJECTED":
            task.rejected_at = None; task.rejection_reason = None
        elif task.rejected_at is None:
            task.rejected_at = timestamp
        if ns != "EXPIRED":
            task.expires_at = None if ns != "PENDING" else task.expires_at
        elif task.expires_at is None:
            task.expires_at = timestamp
        task.status_updated_at = timestamp

    def _unlock_editing(self, *, task, timestamp):
        if task.locked_at is None:
            raise HTTPException(status_code=409, detail="Task is already unlocked")
        task.locked_at = None; task.status_updated_at = timestamp

    def _reassign_vendor(self, db, *, task, assigned_vendor_id, timestamp):
        if not assigned_vendor_id:
            raise HTTPException(status_code=400, detail="assignedVendorId is required for REASSIGN_VENDOR")
        if task.status in {"IN_PROGRESS", "DONE"}:
            raise HTTPException(status_code=409, detail="Task cannot be reassigned in its current state")
        vendor = db.query(Vendor).filter(Vendor.vendor_id == assigned_vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        offering = self._resolve_reassignment_offering(db, task=task, assigned_vendor_id=assigned_vendor_id)
        if offering is None:
            raise HTTPException(status_code=409, detail="No eligible offering found for vendor reassignment")
        latest = (db.query(TaskRequest).filter(TaskRequest.task_id == task.task_id)
                  .order_by(TaskRequest.attempt_no.desc(), TaskRequest.id.desc()).first())
        if latest is None:
            raise HTTPException(status_code=409, detail="Task cannot be reassigned without fulfillment history")
        self._cancel_open_requests(db, task_id=task.task_id)
        task.assigned_vendor_id = assigned_vendor_id; task.selected_offering_id = offering.offering_id
        task.status = "PENDING"; task.rejected_at = None; task.rejection_reason = None
        task.expires_at = None; task.status_updated_at = timestamp
        db.add(TaskRequest(
            package_order_id=latest.package_order_id, task_id=task.task_id,
            vendor_id=assigned_vendor_id, offering_id=offering.offering_id,
            status="SENT", requested_at=timestamp,
            respond_by=timestamp + timedelta(minutes=5), attempt_no=latest.attempt_no + 1,
        ))

    def _resolve_reassignment_offering(self, db, *, task, assigned_vendor_id):
        if task.selected_offering_id:
            s = db.query(Offering).filter(
                Offering.offering_id == task.selected_offering_id,
                Offering.vendor_id == assigned_vendor_id,
                Offering.is_active == True, Offering.is_available == True,
            ).first()
            if s:
                return s
        shortlist = (
            db.query(Offering).join(TaskRecommendation, TaskRecommendation.offering_id == Offering.offering_id)
            .filter(TaskRecommendation.task_id == task.task_id,
                    TaskRecommendation.event_id == task.event_id,
                    Offering.vendor_id == assigned_vendor_id,
                    Offering.is_active == True, Offering.is_available == True)
            .order_by(TaskRecommendation.rank.asc(), Offering.id.asc()).first()
        )
        if shortlist:
            return shortlist
        return db.query(Offering).filter(
            Offering.vendor_id == assigned_vendor_id, Offering.category == task.needs_vendor,
            Offering.currency == task.currency, Offering.is_active == True, Offering.is_available == True,
        ).order_by(Offering.id.asc()).first()

    def _cancel_open_requests(self, db, *, task_id):
        for r in db.query(TaskRequest).filter(
            TaskRequest.task_id == task_id, TaskRequest.status.in_(("SENT", "ACCEPTED"))
        ).all():
            r.status = "CANCELLED"; r.responded_at = now_utc(); db.add(r)

    def _get_latest_package_order_id(self, db, *, task_id):
        r = db.query(TaskRequest).filter(TaskRequest.task_id == task_id).order_by(
            TaskRequest.attempt_no.desc(), TaskRequest.id.desc()).first()
        return r.package_order_id if r else None

    def _get_tasks_by_ids(self, db, *, task_ids):
        if not task_ids:
            return []
        tasks = db.query(Task).filter(Task.task_id.in_(task_ids)).all()
        m = {t.task_id: t for t in tasks}
        return [m[tid] for tid in task_ids if tid in m]


admin_service = AdminService()
