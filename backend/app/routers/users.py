from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import LocalUser

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/current")
def current_user(db: Session = Depends(get_db)):
    user = db.scalars(select(LocalUser).order_by(LocalUser.id.asc())).first()
    return {"id": user.id, "name": user.name, "role": user.role} if user else {"name": "本机用户", "role": "admin"}
