from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Form
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

from app.core.database import SessionLocal
from app.core.dependencies import require_login
from app.models.user import User

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/users")
def users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    # 🔒 Admin-only access
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    users = db.query(User).order_by(User.created_at.desc()).all()

    return request.app.state.templates.TemplateResponse(
        "pages/users.html",
        {
            "request": request,
            "current_user": current_user,
            "users": users
        }
    )

@router.post("/users/create")
def create_user(
    name: str = Form(...),
    employee_id: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check duplicate employee_id
    existing = db.query(User).filter(User.employee_id == employee_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    new_user = User(
        name=name,
        employee_id=employee_id,
        role=role,
        password_hash=hash_password(password)
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse("/users", status_code=303)


@router.post("/users/reset-password")
def reset_password(
    user_id: int = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    

    user.password_hash = hash_password(new_password)
    db.commit()

    return RedirectResponse("/users", status_code=303)

@router.post("/users/disable")
def disable_user(
    user_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    return RedirectResponse("/users", status_code=303)

@router.post("/users/enable")
def enable_user(
    user_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    return RedirectResponse("/users", status_code=303)

@router.post("/users/edit")
def edit_user(
    request: Request,
    user_id: int = Form(...),
    name: str = Form(...),
    employee_id: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # 1️⃣ Fetch user FIRST (IMPORTANT)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session["error"] = "User not found."
        return RedirectResponse("/users", status_code=303)

    # 2️⃣ Prevent self role change (but allow name / employee ID edit)
    if user.id == current_user.id and role != user.role:
        request.session["error"] = "You cannot change your own role."
        return RedirectResponse("/users", status_code=303)

    # 3️⃣ Prevent removing last admin
    if user.role == "admin" and role == "user":
        admin_count = db.query(User).filter(
            User.role == "admin",
            User.is_active == True
        ).count()

        if admin_count <= 1:
            request.session["error"] = "Cannot remove the last admin."
            return RedirectResponse("/users", status_code=303)

    # 4️⃣ Check employee_id uniqueness (exclude this user)
    existing = db.query(User).filter(
        User.employee_id == employee_id,
        User.id != user.id
    ).first()

    if existing:
        request.session["error"] = "Employee ID already exists."
        return RedirectResponse("/users", status_code=303)

    # 5️⃣ Update fields
    user.name = name
    user.employee_id = employee_id
    user.role = role

    db.commit()

    request.session["success"] = "User updated successfully."
    return RedirectResponse("/users", status_code=303)
