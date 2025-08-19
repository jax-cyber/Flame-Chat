from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
import os
import shutil

app = FastAPI()

# CORS for website frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your website domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "data.json"

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"users": {}, "groups": {}, "messages": []}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class UserModel(BaseModel):
    username: str
    password: str

class MessageModel(BaseModel):
    sender: str
    recipient: str  # user or group
    content: str
    group: Optional[bool] = False

# ---------------- User Routes ----------------
@app.post("/register")
def register(user: UserModel):
    if user.username in data["users"]:
        raise HTTPException(status_code=400, detail="User exists")
    data["users"][user.username] = {
        "password": user.password,
        "friends": [],
        "profile_pic": None
    }
    save_data()
    return {"msg": "Registered successfully"}

@app.post("/login")
def login(user: UserModel):
    u = data["users"].get(user.username)
    if not u or u["password"] != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"msg": "Login successful"}

@app.post("/upload_profile_pic/{username}")
def upload_profile_pic(username: str, file: UploadFile = File(...)):
    if username not in data["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    path = f"profile_pics/{username}.png"
    os.makedirs("profile_pics", exist_ok=True)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    data["users"][username]["profile_pic"] = path
    save_data()
    return {"msg": "Profile picture uploaded"}

# ---------------- Friend Routes ----------------
@app.post("/add_friend")
def add_friend(user: str, friend: str):
    if friend not in data["users"] or user not in data["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    if friend not in data["users"][user]["friends"]:
        data["users"][user]["friends"].append(friend)
        data["users"][friend]["friends"].append(user)
        save_data()
    return {"msg": "Friend added"}

# ---------------- Group Routes ----------------
@app.post("/create_group")
def create_group(name: str, members: List[str]):
    if name in data["groups"]:
        raise HTTPException(status_code=400, detail="Group exists")
    data["groups"][name] = {
        "members": members,
        "profile_pic": None
    }
    save_data()
    return {"msg": "Group created"}

@app.post("/upload_group_pic/{group_name}")
def upload_group_pic(group_name: str, file: UploadFile = File(...)):
    if group_name not in data["groups"]:
        raise HTTPException(status_code=404, detail="Group not found")
    path = f"group_pics/{group_name}.png"
    os.makedirs("group_pics", exist_ok=True)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    data["groups"][group_name]["profile_pic"] = path
    save_data()
    return {"msg": "Group picture uploaded"}

# ---------------- Messages ----------------
@app.post("/send_message")
def send_message(msg: MessageModel):
    data["messages"].append(msg.dict())
    save_data()
    return {"msg": "Message sent"}

@app.get("/get_messages/{user_or_group}")
def get_messages(user_or_group: str):
    msgs = [m for m in data["messages"] if m["recipient"] == user_or_group]
    return {"messages": msgs}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
