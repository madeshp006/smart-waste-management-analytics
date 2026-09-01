from fastapi import APIRouter, HTTPException, status, Depends
import psycopg2
import psycopg2.extras
from app.core.security import verify_password, create_access_token, get_current_user, get_db_connection
from app.schemas.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT u.id, u.username, u.email, u.hashed_password, u.role, u.ward_id, w.name as ward_name
        FROM public.users u
        LEFT JOIN public.wards w ON u.ward_id = w.id
        WHERE u.username = %s OR u.email = %s;
    """, (request.username, request.username))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    
    user_dict = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "ward_id": user["ward_id"],
        "ward_name": user["ward_name"]
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user
