import datetime
import secrets
import uuid

import bcrypt
import jwt

JWT_SECRET = "your_secret_key"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode())


def create_jwt(user_id: int, email: str, role: str) -> str:
    payload = {
        "id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=720),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def generate_session_token() -> str:
    return str(uuid.uuid4())


def generate_reset_token() -> str:
    return secrets.token_hex(6)


def token_expiry(minutes: int = 15) -> datetime.datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
