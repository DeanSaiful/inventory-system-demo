from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.dependencies import require_login
from app.models.request import Request as RequestModel
from app.models.component import Component
from app.models.user import User

from fastapi import Form, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/return")
def return_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    query = (
        db.query(RequestModel, Component, User)
        .join(Component, RequestModel.component_id == Component.id)
        .join(User, RequestModel.user_id == User.id)
        .filter(RequestModel.status == "borrowed")
    )

    borrowed_items = query.order_by(RequestModel.requested_at.desc()).all()

    return request.app.state.templates.TemplateResponse(
        "pages/return.html",
        {
            "request": request,
            "current_user": current_user,
            "borrowed_items": borrowed_items
        }
    )

@router.post("/return/confirm")
def confirm_return(
    request_id: int = Form(...),
    return_qty: int = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    req = db.query(RequestModel).filter(RequestModel.id == request_id).first()

    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status != "borrowed":
        raise HTTPException(status_code=400, detail="Request already returned")

    # Permission check
    if current_user.role != "admin" and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if return_qty <= 0:
        raise HTTPException(status_code=400, detail="Invalid return quantity")

    if return_qty > req.quantity:
        raise HTTPException(
            status_code=400,
            detail="Return quantity exceeds borrowed quantity"
        )

    component = db.query(Component).filter(Component.id == req.component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    # Stock update
    component.quantity += return_qty

    # Full return only (for now)
    req.status = "returned"
    req.returned_at = datetime.utcnow()

    db.commit()

    return RedirectResponse("/return", status_code=303)

