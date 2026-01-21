from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.core.database import SessionLocal
from app.core.dependencies import require_login
from app.models.user import User

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- PROFILE PAGE ----------------
@router.get("/profile")
def profile_page(
    request: Request,
    current_user=Depends(require_login)
):
    # admin-only (for now)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return request.app.state.templates.TemplateResponse(
        "pages/profile.html",
        {
            "request": request,
            "current_user": current_user
        }
    )


# ---------------- CHANGE OWN PASSWORD ----------------
@router.post("/profile/password")
def change_own_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    if not verify_password(current_password, current_user.password_hash):
        request.session["error"] = "Current password is incorrect."
        return RedirectResponse("/profile", status_code=303)

    if new_password != confirm_password:
        request.session["error"] = "New password and confirmation do not match."
        return RedirectResponse("/profile", status_code=303)

    user = db.query(User).filter(User.id == current_user.id).first()
    user.password_hash = hash_password(new_password)
    db.commit()

    request.session["success"] = "Password updated successfully."
    return RedirectResponse("/profile", status_code=303)


@router.post("/profile/update")
def update_profile(
    request: Request,
    name: str = Form(...),
    employee_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check employee_id uniqueness (exclude self)
    existing = db.query(User).filter(
        User.employee_id == employee_id,
        User.id != current_user.id
    ).first()

    if existing:
        request.session["error"] = "Employee ID already exists."
        return RedirectResponse("/profile", status_code=303)

    user = db.query(User).filter(User.id == current_user.id).first()
    user.name = name
    user.employee_id = employee_id
    db.commit()

    request.session["success"] = "Profile updated successfully."
    return RedirectResponse("/profile", status_code=303)
