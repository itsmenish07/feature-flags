from database import SessionLocal, engine
from models import Base, FeatureFlag, RemoteConfig

Base.metadata.create_all(bind=engine)

flags = [
    {
        "name": "new_checkout_flow",
        "enabled": True,
        "target_group": "beta",
        "rollout_percentage": 100
    },
    {
        "name": "dark_mode_beta",
        "enabled": False,
        "target_group": "everyone",
        "rollout_percentage": 100
    },
    {
        "name": "ai_recommendations",
        "enabled": True,
        "target_group": "everyone",
        "rollout_percentage": 50
    },
]

configs = [
    {"key": "welcome_message", "value": "Welcome to the demo!"},
    {"key": "announcement", "value": "Summer Sale - 20% off today!"},
]

db = SessionLocal()

added = 0

for f in flags:
    exists = db.query(
        FeatureFlag
    ).filter(
        FeatureFlag.name == f["name"]
    ).first()

    if not exists:
        db.add(FeatureFlag(**f))
        added += 1

for c in configs:
    exists = db.query(
        RemoteConfig
    ).filter(
        RemoteConfig.key == c["key"]
    ).first()

    if not exists:
        db.add(RemoteConfig(**c))
        added += 1

db.commit()
db.close()

print(f"Seed complete. Added {added} new flags/configs.")
print("Now start the server:  uvicorn main:app --reload")
