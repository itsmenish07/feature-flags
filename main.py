from fastapi import FastAPI
from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends
from models import FeatureFlag




from database import engine
from models import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()



@app.get("/flags")
def get_flags(
    db: Session = Depends(get_db)
):
    return db.query(
        FeatureFlag
    ).all()
@app.post("/flags")
def create_flag(
    name: str,
    db: Session = Depends(get_db)
):
    flag = FeatureFlag(
        name=name,
        enabled=False
    )

    db.add(flag)
    db.commit()
    db.refresh(flag)

    return {
    "id": flag.id,
    "name": flag.name,
    "enabled": flag.enabled
}
@app.put("/flags/{flag_id}")
def toggle_flag(
    flag_id: int,
    db: Session = Depends(get_db)
):
    flag = db.query(
        FeatureFlag
    ).filter(
        FeatureFlag.id == flag_id
    ).first()

    if not flag:
        return {
            "error": "Flag not found"
        }

    flag.enabled = not flag.enabled

    db.commit()
    db.refresh(flag)

    return {
    "id": flag.id,
    "name": flag.name,
    "enabled": flag.enabled
}