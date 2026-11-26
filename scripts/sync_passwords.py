from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

passwords = {
    "sathiya@stenovision.ai": "sathiyapassword123",
    "a.thorne@stenovision.org": "thornepassword123",
    "d.chen@stenovision.org": "chenpassword123",
    "h.rostova@stenovision.org": "rostovapassword123",
    "s.martinez@stenovision.org": "martinezpassword123",
}

with SessionLocal() as db:
    for email, pwd in passwords.items():
        u = db.query(User).filter(User.email == email).first()
        if u:
            u.hashed_password = get_password_hash(pwd)
            print("Updated:", email)
    db.commit()
print("Synchronized all passwords successfully!")
