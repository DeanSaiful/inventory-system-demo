import os
import shutil
import re
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi import Query
from fastapi.responses import HTMLResponse

from app.core.dependencies import require_login, require_admin
from app.core.database import SessionLocal
from app.models.component import Component

router = APIRouter()

UPLOAD_DIR = "app/static/uploads/components"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def safe_filename(text: str) -> str:
    """
    Convert text to a filesystem-safe filename.
    Keeps letters, numbers, dot, dash, underscore.
    Replaces everything else with '-'.
    """
    text = text.strip()
    text = re.sub(r"[^\w.-]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


@router.get("/stock")
def stock_page(
    request: Request,
    category: str | None = Query(None),
    description: str | None = Query(None),
    value: str | None = Query(None),
    size: str | None = Query(None),
    voltage: str | None = Query(None),
    watt: str | None = Query(None),
    part_no: str | None = Query(None),
    rack: str | None = Query(None),
    location: str | None = Query(None), 
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    query = db.query(Component)

    if category:
        query = query.filter(Component.category.ilike(f"%{category}%"))
    if description:
        query = query.filter(Component.description.ilike(f"%{description}%"))
    if value:
        query = query.filter(Component.value.ilike(f"%{value}%"))
    if size:
        query = query.filter(Component.size.ilike(f"%{size}%"))
    if voltage:
        query = query.filter(Component.voltage.ilike(f"%{voltage}%"))
    if watt:
        query = query.filter(Component.watt.ilike(f"%{watt}%"))
    if part_no:
        query = query.filter(Component.part_no.ilike(f"%{part_no}%"))
    if rack:
        query = query.filter(Component.rack.ilike(f"%{rack}%"))
    if location:
        query = query.filter(Component.location.ilike(f"%{location}%"))

    components = query.all()

    return request.app.state.templates.TemplateResponse(
        "pages/stock.html",
        {
            "request": request,
            "current_user": current_user,
            "components": components,
            "filters": {
                "category": category or "",
                "description": description or "",
                "value": value or "",
                "size": size or "",
                "voltage": voltage or "",
                "watt": watt or "",
                "part_no": part_no or "",
                "rack": rack or "",
                "location": location or "" 
                
            }
        }
    )


@router.post("/stock/add")
def add_component(
    request: Request,
    category: str = Form(...),
    description: str = Form(...),
    value: str = Form(None),
    size: str = Form(None),
    voltage: str = Form(None),
    watt: str = Form(None),
    type: str = Form(None),
    part_no: str = Form(...),
    rack: str = Form(None),
    location: str = Form(None),
    quantity: int = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403)

    # Check duplicate part no
    existing = db.query(Component).filter(Component.part_no == part_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="Part No already exists")

    image_path = None

    if image:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        ext = os.path.splitext(image.filename)[1].lower()

        safe_part_no = safe_filename(part_no)
        filename = f"{safe_part_no}{ext}"

        file_path = os.path.join(UPLOAD_DIR, filename)


        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        image_path = f"uploads/components/{filename}"

    component = Component(
        category=category,
        description=description,
        value=value,
        size=size,
        voltage=voltage,
        watt=watt,
        type=type,
        part_no=part_no,
        rack=rack,
        location=location,
        quantity=quantity,
        image_path=image_path
    )

    from fastapi.responses import RedirectResponse

    db.add(component)
    db.commit()

    return RedirectResponse("/stock", status_code=303)

@router.post("/stock/edit/{component_id}")
def edit_component(
    component_id: int,
    request: Request,
    category: str = Form(...),
    description: str = Form(...),
    value: str = Form(None),
    size: str = Form(None),
    voltage: str = Form(None),
    watt: str = Form(None),
    type: str = Form(None),
    part_no: str = Form(...),
    rack: str = Form(None),
    location: str = Form(None),
    quantity: int = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)

    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404)

    # Update fields
    component.category = category
    component.description = description
    component.value = value
    component.size = size
    component.voltage = voltage
    component.watt = watt
    component.type = type
    component.part_no = part_no
    component.rack = rack
    component.location = location
    component.quantity = quantity

    # Handle image replace
    if image:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        ext = os.path.splitext(image.filename)[1].lower()

        safe_part_no = safe_filename(part_no)
        filename = f"{safe_part_no}{ext}"

        file_path = os.path.join(UPLOAD_DIR, filename)


        # Delete old image if exists
        if component.image_path:
            old_path = os.path.join("app/static", component.image_path)
            if os.path.exists(old_path):
                os.remove(old_path)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        component.image_path = f"uploads/components/{filename}"

    db.commit()
    return RedirectResponse("/stock", status_code=303)

@router.post("/stock/delete/{component_id}")
def delete_component(
    component_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403)

    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404)

    # Delete image file
    if component.image_path:
        image_file = os.path.join("app/static", component.image_path)
        if os.path.exists(image_file):
            os.remove(image_file)

    db.delete(component)
    db.commit()

    return RedirectResponse("/stock", status_code=303)


@router.get("/stock/edit/{component_id}", response_class=HTMLResponse)
def edit_component_form(
    request: Request,
    component_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_login)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    component = db.query(Component).filter(Component.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    return request.app.state.templates.TemplateResponse(
        "pages/stock_edit.html",
        {
            "request": request,
            "component": component,
            "current_user": current_user   # 👈 ADD THIS
        }
    )

