"""通用安全原语：密码哈希与 JWT 编解码。

本文件不知道"user"是什么，也不知道 token 里放什么——那由 services/auth_service.py
决定；这里只提供可整体复制的原语。
"""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

_JWT_ALGORITHM = "HS256"


def hash_password(raw: str) -> str:
    """bcrypt 哈希（自动加盐，返回含算法参数的字符串）。

    注：不经 passlib（1.7.4 与 bcrypt 4.x 不兼容且已停止维护）。
    """
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        return False


def jwt_encode(payload: dict, expires_delta: timedelta) -> str:
    """附带 iat/exp 声明的 HS256 签名。"""
    now = datetime.now(timezone.utc)
    data = {**payload, "iat": now, "exp": now + expires_delta}
    return jwt.encode(data, _secret(), algorithm=_JWT_ALGORITHM)


def jwt_decode(token: str) -> dict:
    """验签 + 过期检查；失败抛 jwt 异常，由调用方翻译。"""
    return jwt.decode(token, _secret(), algorithms=[_JWT_ALGORITHM])


def _secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET 未配置，请检查 .env 文件")
    return secret
