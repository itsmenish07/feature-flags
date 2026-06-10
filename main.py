from fastapi import FastAPI
from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends
from models import FeatureFlag
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from websocket_manager import manager
from models import (
    FeatureFlag,
    RemoteConfig
)




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
async def toggle_flag(
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

    await manager.broadcast(
    {
        "type": "flag_update",
        "id": flag.id,
        "name": flag.name,
        "enabled": flag.enabled
    }
)

    return {
    "id": flag.id,
    "name": flag.name,
    "enabled": flag.enabled
}
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):
    await manager.connect(
        websocket
    )

    print("Client connected")

    try:

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(
            websocket
        )

        print("Client disconnected")
    
@app.post("/broadcast")
async def broadcast_test():

    await manager.broadcast(
        {
            "message": "Hello from server"
        }
    )

    return {
        "status": "sent"
    }

@app.post("/configs")
def create_config(
    key: str,
    value: str,
    db: Session = Depends(get_db)
):

    config = RemoteConfig(
        key=key,
        value=value
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return config

@app.get("/configs")
def get_configs(
    db: Session = Depends(get_db)
):

    return db.query(
        RemoteConfig
    ).all()

@app.put("/configs/{config_id}")
async def update_config(
    config_id: int,
    value: str,
    db: Session = Depends(get_db)
):

    config = db.query(
        RemoteConfig
    ).filter(
        RemoteConfig.id == config_id
    ).first()

    if not config:
        return {
            "error": "not found"
        }

    config.value = value

    db.commit()
    db.refresh(config)

    await manager.broadcast(
        {
            "type": "config_update",
            "id": config.id,
            "key": config.key,
            "value": config.value
        }
    )

    return config