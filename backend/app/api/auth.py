from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime

from app.models.schemas import UserCreate, UserLogin, Token, UserOut
from app.utils.auth import hash_password, verify_password, create_access_token
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    db = get_db()
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    doc = {
        "name": user.name,
        "company": user.company,
        "email": user.email,
        "password": hashed,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)

    token = create_access_token({"sub": user_id, "email": user.email})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut(id=user_id, name=user.name, company=user.company, email=user.email),
    )


@router.post("/login", response_model=Token)
async def login(creds: UserLogin):
    db = get_db()
    user_doc = await db.users.find_one({"email": creds.email})
    if not user_doc or not verify_password(creds.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user_doc["_id"])
    token = create_access_token({"sub": user_id, "email": creds.email})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut(id=user_id, name=user_doc["name"], company=user_doc["company"], email=user_doc["email"]),
    )
