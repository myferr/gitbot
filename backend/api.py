from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse
from pymongo import MongoClient
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import os, requests, time

# Load environment variables
load_dotenv()

app = FastAPI()
mongo = MongoClient(os.getenv("MONGO_URI"))
users = mongo.gitbot.users

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
BACKEND = os.getenv("BACKEND_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

fernet = Fernet(ENCRYPTION_KEY)

@app.get("/auth")
def auth(discord: str):
    redirect_uri = f"https://{BACKEND}/callback?discord={discord}"
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=repo"
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str, discord: str):
    # Step 1: Exchange code for token
    token_res = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        }
    )
    token_json = token_res.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return HTMLResponse("❌ Failed to get token", status_code=400)

    # Step 2: Fetch user info
    user_res = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}"}
    )
    user_json = user_res.json()

    if "login" not in user_json:
        return HTMLResponse("❌ Failed to fetch user", status_code=400)

    # Step 3: Encrypt token
    encrypted_token = fernet.encrypt(access_token.encode('utf-8'))

    # Step 4: Save encrypted token to DB
    users.update_one(
        {"discord_id": discord},
        {
            "$set": {
                "github_id": user_json["id"],
                "github_user": user_json["login"],
                "avatar_url": user_json["avatar_url"],
                "token": encrypted_token,
                "linked_at": time.time()
            }
        },
        upsert=True
    )

    return RedirectResponse(f"https://thegitbot.vercel.app/auth/complete?discord={user_json['login']}")

