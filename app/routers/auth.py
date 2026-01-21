from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session


from app.core.dependencies import get_db
from app.core.security import verify_password
from app.models.user import User

router = APIRouter()

@router.get("/")
def login_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "base.html",
        {"request": request}
    )

@router.post("/login")
def login(
    request: Request,
    employee_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    user = db.query(User).filter(User.employee_id == employee_id).first()

    if not user or not verify_password(password, user.password_hash):
        request.session["error"] = "Invalid username or password."
        return RedirectResponse("/", status_code=303)

    if not user.is_active:
        request.session["error"] = "Your account is disabled. Please contact admin."
        return RedirectResponse("/", status_code=303)


    request.session["user_id"] = user.id
    return RedirectResponse("/request", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

