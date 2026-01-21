from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()

admin = User(
    name="admin",
    employee_id="bpe252610",
    role="admin",
    password_hash=hash_password("admin123")
)

db.add(admin)
db.commit()
db.close()
