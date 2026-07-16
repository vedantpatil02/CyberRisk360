from datetime import datetime, timedelta, timezone

from app.core.constants import (
    ALL_ROLES,
    MAX_FAILED_LOGIN_ATTEMPTS,
    ACCOUNT_LOCKOUT_MINUTES,
)
from app.repositories.users.user_repository import (
    get_by_email,
    create_user
)
from app.services.security.security import (
    hash_password,
    verify_password
)

VALID_ROLES = list(ALL_ROLES)


# Login outcomes returned by `attempt_login`. `None` (no error) means
# the credentials were accepted.
LOGIN_INVALID = "invalid"
LOGIN_LOCKED = "locked"
LOGIN_INACTIVE = "inactive"


def register_user(db, user, org_id):
    """
    Create a new user account in an organization.

    Assumes the caller (API layer) has already validated that the
    email is unique, the role is valid, and the org exists - this just
    does the write.
    """

    created_user = create_user(
        db,
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role,
        org_id=org_id
    )

    return created_user


def _utcnow():
    return datetime.now(timezone.utc)


def _as_aware(value):
    """
    Normalize a datetime read back from the DB to timezone-aware UTC.

    PostgreSQL returns aware datetimes; SQLite returns naive ones. This
    lets lockout comparisons work identically on both.
    """

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def is_account_locked(user):
    """
    True if the account is currently within an active lockout window.
    """

    locked_until = _as_aware(user.locked_until)

    return locked_until is not None and locked_until > _utcnow()


def _clear_expired_lock(db, user):
    """
    If a past lockout has elapsed, reset the counter so the next attempt
    starts fresh instead of re-locking on the first failure.
    """

    locked_until = _as_aware(user.locked_until)

    if locked_until is not None and locked_until <= _utcnow():
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()


def register_failed_login(db, user):
    """
    Count a failed login and lock the account once the threshold is hit.
    Returns True if this failure triggered a lockout.
    """

    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

    locked = False

    if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = _utcnow() + timedelta(
            minutes=ACCOUNT_LOCKOUT_MINUTES
        )
        locked = True

    db.commit()

    return locked


def register_successful_login(db, user):
    """
    Clear failure state and stamp the last-login time.
    """

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = _utcnow()

    db.commit()


def attempt_login(db, email, password):
    """
    Attempt to authenticate. Returns `(user, error)` where `error` is
    one of LOGIN_INVALID / LOGIN_LOCKED / LOGIN_INACTIVE, or `None` on
    success. `user` is `None` only when the email is unknown.

    Side effects (lockout counter, last-login) are persisted here.
    """

    user = get_by_email(db, email)

    if not user:
        return None, LOGIN_INVALID

    if not user.is_active:
        return user, LOGIN_INACTIVE

    _clear_expired_lock(db, user)

    if is_account_locked(user):
        return user, LOGIN_LOCKED

    if not verify_password(password, user.password):
        register_failed_login(db, user)
        return user, LOGIN_INVALID

    register_successful_login(db, user)

    return user, None


def authenticate_user(db, email, password):
    """
    Backwards-compatible helper: return the User if the credentials are
    valid and the account is usable, else None. Prefer `attempt_login`
    where the specific failure reason matters (e.g. the login endpoint).
    """

    user, error = attempt_login(db, email, password)

    return user if error is None else None


def change_password(db, user, new_password):
    """
    Set a new password hash for a user.
    """

    user.password = hash_password(new_password)
    db.commit()

    return user


def set_active(db, user, is_active: bool):
    """
    Activate or deactivate an account. Deactivating also clears any
    lockout state (a deactivated account is rejected regardless).
    """

    user.is_active = is_active

    if is_active:
        user.failed_login_attempts = 0
        user.locked_until = None

    db.commit()

    return user


def update_role(db, user, role: str):
    """
    Change a user's role.
    """

    user.role = role
    db.commit()

    return user
