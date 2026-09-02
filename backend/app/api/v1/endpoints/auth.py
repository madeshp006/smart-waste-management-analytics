from fastapi import APIRouter, HTTPException, status, Depends
from app.core.security import verify_password, create_access_token, get_current_user
from app.db.connection import get_db, execute_query
from app.schemas.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    conn, engine_type = get_db()
    users_table = "public.users" if engine_type == "postgres" else "users"
    wards_table = "public.wards" if engine_type == "postgres" else "wards"

    sql = f"""
        SELECT u.id, u.username, u.email, u.hashed_password, u.role, u.ward_id, w.name as ward_name
        FROM {users_table} u
        LEFT JOIN {wards_table} w ON u.ward_id = w.id
        WHERE u.username = %s OR u.email = %s;
    """
    user = execute_query(sql, (request.username, request.username), fetch="one")

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
