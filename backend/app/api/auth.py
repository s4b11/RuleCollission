from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Organization, StaffUser
from ..security import check_password, current_staff, make_token

router = APIRouter(prefix="/auth", tags=["auth"])


class Login(BaseModel):
    email: str
    password: str


def staff_view(db: Session, user: StaffUser) -> dict:
    org = db.get(Organization, user.org_id)
    return {
        "id": user.id, "name": user.name, "email": user.email, "role": user.role, "office": user.office,
        "is_admin": user.is_admin, "organization": org.name, "subject_label": org.subject_label,
    }


@router.post("/login")
def login(body: Login, db: Session = Depends(get_db)):
    user = db.scalars(select(StaffUser).where(StaffUser.email == body.email.lower().strip())).first()
    if not user or not check_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(user), "staff": staff_view(db, user)}


@router.get("/me")
def me(user: StaffUser = Depends(current_staff), db: Session = Depends(get_db)):
    return staff_view(db, user)
