from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import uuid
import re
import re
from datetime import datetime, timezone

app = FastAPI(
    title="User Management + Text Analysis API",
    description="In-memory User Management with Text Analysis capabilities",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "online", "message": "User Management & Text Analysis API is running."}

# ─────────────────────────────────────────────
#  In-Memory Storage
# ─────────────────────────────────────────────
users_db: dict = {}          # { user_id: {...user data...} }
analyses_db: dict = {}       # { analysis_id: {...analysis data...} }

# ─────────────────────────────────────────────
#  Pydantic Schemas
# ─────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: str

class TextAnalysisRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text field must not be empty.")
        if len(v) > 200:
            raise ValueError("Text must not exceed 200 characters.")
        return v

class TextAnalysisResponse(BaseModel):
    analysis_id: str
    user_id: str
    text: str
    word_count: int
    uppercase_count: int
    special_character_count: int
    analyzed_at: str


# ─────────────────────────────────────────────
#  Helper: Text Analysis Logic
# ─────────────────────────────────────────────
def analyze_text(text: str) -> dict:
    word_count = len(text.split())
    uppercase_count = sum(1 for c in text if c.isupper())
    special_character_count = len(re.findall(r'[^a-zA-Z0-9\s]', text))
    return {
        "word_count": word_count,
        "uppercase_count": uppercase_count,
        "special_character_count": special_character_count,
    }


# ─────────────────────────────────────────────
#  User Management Endpoints
# ─────────────────────────────────────────────

@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate):
    """Create a new user with auto-generated unique ID."""
    # Check for duplicate email
    for user in users_db.values():
        if user["email"] == payload.email:
            raise HTTPException(
                status_code=400,
                detail=f"A user with email '{payload.email}' already exists."
            )

    user_id = str(uuid.uuid4())
    user_record = {
        "id": user_id,
        "name": payload.name,
        "email": payload.email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis_ids": []   # track all analyses for this user
    }
    users_db[user_id] = user_record
    return UserResponse(**user_record)


@app.get("/users", response_model=list[UserResponse], status_code=200)
def get_all_users(limit: int = 10, offset: int = 0, sort: str = "asc"):
    """
    Return all users with pagination and sorting.
    - limit: number of records to return (default 10, must be > 0)
    - offset: starting index (default 0, must be >= 0)
    - sort: sort order by user_id (asc or desc)
    """
    # Validation
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be a positive integer.")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be zero or a positive integer.")
    if sort not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="sort must be either 'asc' or 'desc'.")

    # Fetch and Sort
    users = list(users_db.values())
    users.sort(key=lambda x: x["id"], reverse=(sort == "desc"))

    # Paginate
    return [UserResponse(**u) for u in users[offset : offset + limit]]


@app.get("/users/{user_id}", response_model=UserResponse, status_code=200)
def get_user(user_id: str):
    """Return a single user by ID."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found.")
    return UserResponse(**user)


@app.delete("/users/{user_id}", status_code=200)
def delete_user(user_id: str):
    """Delete a user and all their associated analyses."""
    user = users_db.pop(user_id, None)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found.")

    # Remove all analyses linked to this user
    for aid in user.get("analysis_ids", []):
        analyses_db.pop(aid, None)

    return {"message": f"User '{user['name']}' (ID: {user_id}) deleted successfully."}


# ─────────────────────────────────────────────
#  Text Analysis Endpoint (per user)
# ─────────────────────────────────────────────

@app.post("/users/{user_id}/analyze", response_model=TextAnalysisResponse, status_code=201)
def analyze_user_text(user_id: str, payload: TextAnalysisRequest):
    """
    Perform text analysis for a specific user.
    Returns word count, uppercase character count, and special character count.
    Each analysis is stored and linked to the user.
    """
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found.")

    stats = analyze_text(payload.text)
    analysis_id = str(uuid.uuid4())
    analysis_record = {
        "analysis_id": analysis_id,
        "user_id": user_id,
        "text": payload.text,
        "word_count": stats["word_count"],
        "uppercase_count": stats["uppercase_count"],
        "special_character_count": stats["special_character_count"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    analyses_db[analysis_id] = analysis_record
    users_db[user_id]["analysis_ids"].append(analysis_id)

    return TextAnalysisResponse(**analysis_record)


@app.get("/users/{user_id}/analyses", response_model=list[TextAnalysisResponse], status_code=200)
def get_user_analyses(
    user_id: str, 
    limit: int = 10, 
    offset: int = 0, 
    sort: str = "asc", 
    min_words: Optional[int] = None
):
    """
    Return all text analyses for a specific user with filtering, sorting, and pagination.
    - min_words: filter analyses by minimum word count (must be >= 0)
    - limit: number of records to return (default 10, must be > 0)
    - offset: starting index (default 0, must be >= 0)
    - sort: sort order by analysis_id (asc or desc)
    """
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID '{user_id}' not found.")

    # Validation
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be a positive integer.")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be zero or a positive integer.")
    if sort not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="sort must be either 'asc' or 'desc'.")
    if min_words is not None and min_words < 0:
        raise HTTPException(status_code=400, detail="min_words must be zero or a positive integer.")

    # Fetch analyses
    analyses = [
        analyses_db[aid] 
        for aid in user.get("analysis_ids", []) 
        if aid in analyses_db
    ]

    # Filtering (Applied before pagination)
    if min_words is not None:
        analyses = [a for a in analyses if a["word_count"] >= min_words]

    # Sorting (By analysis_id)
    analyses.sort(key=lambda x: x["analysis_id"], reverse=(sort == "desc"))

    # Pagination
    paginated_results = analyses[offset : offset + limit]

    return [TextAnalysisResponse(**a) for a in paginated_results]
