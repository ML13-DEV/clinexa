from app.core.security import hash_password
from app.database import SessionLocal
from app.models.usuario import Usuario

db = SessionLocal()

user = Usuario(
    username="admin",
    password=hash_password("1234"),
    rol="owner",
    especialidad="sistema"
)

db.add(user)
db.commit()

print("Admin creado ✅")
