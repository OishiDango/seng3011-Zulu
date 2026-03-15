from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr

from auth_utils import (create_jwt, generate_reset_token,
                        generate_session_token, hash_password, token_expiry,
                        verify_password)
from database import get_db

app = FastAPI()


# ------------------------------
# Schemas
# ------------------------------
class SignupSchema(BaseModel):
    email: EmailStr
    password: str
    subscribed: bool = False


class SigninSchema(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetSchema(BaseModel):
    email: EmailStr
    token: str
    new_password: str


# ------------------------------
# Signup
# ------------------------------
@app.post("/signup")
def signup(data: SignupSchema):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s", (data.email.lower(),))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(data.password)

    cursor.execute(
        "INSERT INTO users (email, password, subscribed) VALUES (%s, %s, %s)",
        (data.email.lower(), hashed_password, data.subscribed),
    )
    conn.commit()
    conn.close()

    return {"message": "User created successfully", "email": data.email}


# ------------------------------
# Signin
# ------------------------------
@app.post("/signin")
def signin(data: SigninSchema):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s", (data.email.lower(),))
    user = cursor.fetchone()
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_jwt(user["id"], user["email"], user["role"])
    session_token = generate_session_token()

    cursor.execute(
        "INSERT INTO sessions (user_id, session_token) VALUES (%s, %s)",
        (user["id"], session_token),
    )
    conn.commit()
    conn.close()

    return {
        "message": "Sign-in successful",
        "token": token,
        "sessionToken": session_token,
    }


# ------------------------------
# Signout
# ------------------------------
@app.post("/signout")
def signout(x_session_id: str = Header(...)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions WHERE session_token = %s", (x_session_id,))
    session = cursor.fetchone()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    cursor.execute("DELETE FROM sessions WHERE session_token = %s", (x_session_id,))
    conn.commit()
    conn.close()

    return {"message": "Successfully signed out"}


# ------------------------------
# Password reset request
# ------------------------------
@app.post("/password-reset/request")
def request_password_reset(data: PasswordResetRequestSchema):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s", (data.email.lower(),))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Remove old tokens
    cursor.execute(
        "DELETE FROM password_reset_tokens WHERE email = %s", (data.email.lower(),)
    )

    token = generate_reset_token()
    expires_at = token_expiry()

    cursor.execute(
        "INSERT INTO password_reset_tokens (email, token, expires_at) "
        "VALUES (%s, %s, %s)",
        (data.email.lower(), token, expires_at),
    )
    conn.commit()
    conn.close()

    print(f"Password reset token for {data.email}: {token}")  # In production, email it

    return {"message": "Password reset token generated and sent"}


# ------------------------------
# Password reset
# ------------------------------
@app.post("/password-reset/reset")
def reset_password(data: PasswordResetSchema):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM password_reset_tokens WHERE email = %s AND token = %s "
        "AND expires_at > %s",
        (data.email.lower(), data.token, datetime.utcnow()),
    )
    token_row = cursor.fetchone()
    if not token_row:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    hashed_password = hash_password(data.new_password)
    cursor.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (hashed_password, data.email.lower()),
    )
    cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (data.token,))
    conn.commit()
    conn.close()

    return {"message": "Password updated successfully"}
