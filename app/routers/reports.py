from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook

from app.core.database import SessionLocal
from app.core.dependencies import require_login
from app.models.component import Component
from app.models.request import Request as RequestModel
from app.models.user import User

router = APIRouter(prefix="/reports")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= REPORT PAGE =================
@router.get("")
def reports_page(
    request: Request,
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return request.app.state.templates.TemplateResponse(
        "pages/reports.html",
        {
            "request": request,
            "current_user": current_user
        }
    )


# ================= COMPONENT EXCEL =================
@router.get("/components/excel")
def export_components_excel(
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    components = db.query(Component).order_by(Component.category, Component.part_no).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Components"

    ws.append([
        "Category", "Description", "Value", "Size",
        "Voltage", "Watt", "Type", "Part No",
        "Rack", "Location", "Quantity", "Created At"
    ])

    for c in components:
        ws.append([
            c.category,
            c.description,
            c.value,
            c.size,
            c.voltage,
            c.watt,
            c.type,
            c.part_no,
            c.rack,
            c.location,
            c.quantity,
            c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
        ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"components_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ================= TRANSACTION EXCEL =================
@router.get("/transactions/excel")
def export_transactions_excel(
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    transactions = (
        db.query(RequestModel, Component, User)
        .join(Component, RequestModel.component_id == Component.id)
        .join(User, RequestModel.user_id == User.id)
        .order_by(RequestModel.requested_at.desc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"

    ws.append([
        "Request ID", "Category", "Part No", "Description",
        "Borrowed By", "Employee ID",
        "Quantity", "Borrowed At", "Returned At", "Status"
    ])

    for r, c, u in transactions:
        ws.append([
            r.id,
            c.category,
            c.part_no,
            c.description,
            u.name,
            u.employee_id,
            r.quantity,
            r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
            r.returned_at.strftime("%Y-%m-%d %H:%M") if r.returned_at else "",
            r.status
        ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
