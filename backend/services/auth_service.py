"""认证服务：注册、登录校验、token 签发与解析（项目决策层）。

与 utils/security.py 的分工：
- security 只提供原语（哈希、JWT 编解码），不知道"user"是什么；
- 本层做项目决策：token 放什么声明、有效期多久、允许哪些角色。
"""
import os
from datetime import timedelta

import jwt

from models import user as user_model
from utils import security

ALLOWED_ROLES = ("employee", "finance")


class AuthError(Exception):
    """token 无效/过期的统一异常，由 api/deps.py 翻译为 401。"""


def register(username: str, password: str, role: str = "employee") -> dict:
    """注册新用户；返回不含密码哈希的用户 dict。"""
    if role not in ALLOWED_ROLES:
        raise ValueError(f"不支持的角色: {role}")
    if user_model.get_by_name(username):
        raise ValueError("用户名已存在")
    uid = user_model.create(username, security.hash_password(password), role)
    return user_model.get(uid)


def authenticate(username: str, password: str):
    """登录校验：成功返回用户行，失败返回 None（不区分失败原因，防账号枚举）。"""
    user = user_model.get_by_name(username)
    if user and security.verify_password(password, user["password"]):
        return user
    return None


def create_token(user) -> str:
    """签发 JWT：声明 sub(用户名)/uid/role，有效期取 JWT_EXPIRE_DAYS（天）。"""
    days = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
    return security.jwt_encode(
        {"sub": user["username"], "uid": user["id"], "role": user["role"]},
        timedelta(days=days),
    )


def decode_token(token: str) -> dict:
    """解析并校验 JWT；任何失败统一抛 AuthError。"""
    try:
        payload = security.jwt_decode(token)
    except jwt.ExpiredSignatureError:
        raise AuthError("登录已过期，请重新登录") from None
    except jwt.InvalidTokenError:
        raise AuthError("无效的登录凭证") from None
    if not payload.get("sub"):
        raise AuthError("无效的登录凭证")
    return payload
