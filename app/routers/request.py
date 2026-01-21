from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from math import ceil
from fastapi import Query


from app.core.dependencies import require_login
from app.core.database import SessionLocal
from app.models.component import Component
from app.models.request import Request as RequestModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# GET: Request page
# =========================
PAGE_SIZE = 20

@router.get("/request")
def request_page(
    request: Request,
    page: int = 1,

    category: str | None = Query(None),
    description: str | None = Query(None),
    part_no: str | None = Query(None),
    rack: str | None = Query(None),

    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    query = db.query(Component)

    if category:
        query = query.filter(Component.category.ilike(f"%{category}%"))
    if description:
        query = query.filter(Component.description.ilike(f"%{description}%"))
    if part_no:
        query = query.filter(Component.part_no.ilike(f"%{part_no}%"))
    if rack:
        query = query.filter(Component.rack.ilike(f"%{rack}%"))

    total = query.count()
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    page = max(1, min(page, total_pages))

    components = (
        query
        .order_by(Component.category, Component.part_no)
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        "pages/request.html",
        {
            "request": request,
            "current_user": current_user,
            "components": components,
            "page": page,
            "total_pages": total_pages,
            "filters": {
                "category": category or "",
                "description": description or "",
                "part_no": part_no or "",
                "rack": rack or ""
            }
        }
    )




# =========================
# POST: Create request
# =========================
@router.post("/request/create")
def create_request(
    component_id: int = Form(...),
    quantity: int = Form(...),
    remarks: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if quantity <= 0:
        raise HTTPException(status_code=400)

    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404)

    if quantity > component.quantity:
        raise HTTPException(status_code=400)

    component.quantity -= quantity

    req = RequestModel(
        user_id=current_user.id,
        component_id=component.id,
        quantity=quantity,
        status="borrowed",
        remarks=remarks
    )


    db.add(req)
    db.commit()

    return RedirectResponse("/request", status_code=303)
