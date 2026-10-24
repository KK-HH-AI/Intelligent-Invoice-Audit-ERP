"""HTTP 鉴权插销：从请求取 Bearer token → 校验 → 注入当前用户。

只做"取 token + 抛 401/403"，无任何业务判断；角色白名单由各端点声明。
"""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from services import auth_service

# tokenUrl 仅供 FastAPI 文档页（/docs）的登录交互使用
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """解析 Bearer token，返回 {id, username, role}；失败抛 401。"""
    try:
        payload = auth_service.decode_token(token)
    except auth_service.AuthError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return {
        "id": payload.get("uid"),
        "username": payload["sub"],
        "role": payload.get("role", "employee"),
    }


def require_role(*roles: str):
    """角色准入工厂：require_role('finance') 限制仅财务可访问，违规抛 403。"""
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="无权限执行此操作")
        return user

    return checker
