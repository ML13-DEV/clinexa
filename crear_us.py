from app.auth import hash_password
from app.database import SessionLocal
from app.models.usuario import Usuario

db = SessionLocal()

user = Usuario(
    username="eugepoli",
    password=hash_password("eugeniaHematologia")
)

db.add(user)
db.commit()