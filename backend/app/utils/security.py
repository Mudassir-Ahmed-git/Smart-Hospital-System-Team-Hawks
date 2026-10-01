"""Password hashing, JWT handling and role-based access control dependencies."""
from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models.user import User
from app.utils.helpers import utcnow

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/token")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], password_hash.encode())
    except ValueError:
        return False


def create_access_token(user: User) -> str:
    expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "role": user.role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error
    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


def require_roles(*roles: str):
    """Dependency factory. Admin always passes."""
    allowed = set(roles) | {"admin"}

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires one of roles: {', '.join(sorted(allowed))}")
        return user

    return checker


def ensure_hospital_access(user: User, hospital_id: int) -> None:
    """Hospital staff may only touch their own hospital; admins may touch any."""
    if user.role == "admin":
        return
    if user.role == "hospital" and user.hospital_id == hospital_id:
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only manage your own hospital")
