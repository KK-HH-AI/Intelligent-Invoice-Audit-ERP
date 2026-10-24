"""认证路由：注册 / 登录。"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    role: str = "employee"


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(body: RegisterIn):
    """注册；成功返回不含密码哈希的用户信息。"""
    try:
        user = auth_service.register(body.username, body.password, body.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }


@router.post("/login")
def login(body: LoginIn):
    """登录；成功返回 JWT 与用户角色。"""
    user = auth_service.authenticate(body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {
        "token": auth_service.create_token(user),
        "username": user["username"],
        "role": user["role"],
    }
