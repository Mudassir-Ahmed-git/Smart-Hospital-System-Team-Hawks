from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models.hospital import Hospital
from app.models.user import User
from app.schemas.user_schema import LoginIn, RegisterIn, TokenOut, UserOut
from app.utils.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

ROLE_LABEL = {"patient": "Patient", "hospital": "Hospital staff", "ambulance": "Ambulance coordinator", "admin": "Administrator"}


def _token_response(user: User) -> dict:
    token = create_access_token(user)
    return {"token": token, "access_token": token, "token_type": "bearer", "user": user}


def _find_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.lower()))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create user")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role != "patient" and not settings.ALLOW_OPEN_ROLE_REGISTRATION:
        raise HTTPException(403, "Only patient accounts can self-register. Ask an administrator for a staff account.")
    if _find_user(db, data.email):
        raise HTTPException(409, "An account with this email already exists")

    hospital_id = None
    if data.role == "hospital":
        hospital_id = data.hospital_id or settings.DEFAULT_STAFF_HOSPITAL_ID
        if not db.get(Hospital, hospital_id):
            raise HTTPException(422, f"Hospital {hospital_id} does not exist")
    user = User(name=data.name.strip(), email=data.email.lower(), password_hash=hash_password(data.password),
                role=data.role, hospital_id=hospital_id)
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=TokenOut, summary="JWT login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = _find_user(db, data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if data.role and data.role != user.role:
        raise HTTPException(403, f"This account is registered as {ROLE_LABEL[user.role]}. Choose that role to sign in.")
    return _token_response(user)


@router.post("/token", response_model=TokenOut, include_in_schema=True, summary="OAuth2 form login (Swagger 'Authorize' button)")
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = _find_user(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return _token_response(user)


@router.get("/me", response_model=UserOut, summary="Current user")
def me(user: User = Depends(get_current_user)):
    return user
