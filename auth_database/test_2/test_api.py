# mypy: disable-error-code="import"
import requests

BASE_URL = "http://127.0.0.1:8000"


# ---------------------------
# 1 Signup
# ---------------------------
signup_data = {
    "email": "marcushu@example.com",
    "password": "marcuspassword123",
    "subscribed": True,
}

signup_resp = requests.post(f"{BASE_URL}/signup", json=signup_data)
print("Signup response:", signup_resp.json())


# ---------------------------
# 2 Signin
# ---------------------------
signin_data = {
    "email": "alice@example.com",
    "password": "MyStrongPassword123",
}

signin_resp = requests.post(f"{BASE_URL}/signin", json=signin_data)
signin_result = signin_resp.json()
print("Signin response:", signin_result)

# Store session token
session_token = signin_result.get("sessionToken")


# ---------------------------
# 3 Signout
# ---------------------------
if session_token:
    headers = {"x-session-id": session_token}
    signout_resp = requests.post(f"{BASE_URL}/signout", headers=headers)
    print("Signout response:", signout_resp.json())


# ---------------------------
# 4 Password reset request
# ---------------------------
reset_request_data = {"email": "alice@example.com"}
reset_request_resp = requests.post(
    f"{BASE_URL}/password-reset/request", json=reset_request_data
)
print("Password reset request response:", reset_request_resp.json())

# IMPORTANT: Check your terminal running FastAPI — the token is printed there
reset_token = input("Enter the password reset token shown in the terminal: ")


# ---------------------------
# 5 Password reset
# ---------------------------
reset_data = {
    "email": "alice@example.com",
    "token": reset_token,
    "new_password": "NewStrongPassword456",
}

reset_resp = requests.post(f"{BASE_URL}/password-reset/reset", json=reset_data)
print("Password reset response:", reset_resp.json())


# ---------------------------
# 6 Signin again with new password
# ---------------------------
signin_data_new = {
    "email": "alice@example.com",
    "password": "NewStrongPassword456",
}

signin_resp_new = requests.post(f"{BASE_URL}/signin", json=signin_data_new)
print("Signin with new password response:", signin_resp_new.json())
