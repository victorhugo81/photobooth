from models import init_db, Event, Photo
from pathlib import Path

Session = init_db(Path("photobooth.db"))

with Session() as s:
    print("=== Events ===")
    for e in s.query(Event).all():
        print(e.to_dict())

    print("\n=== Photos (last 10) ===")
    for p in s.query(Photo).order_by(Photo.timestamp.desc()).limit(10).all():
        print(p.to_dict())