"""用户实体：注册用。密码字段只接收哈希，明文不进入模型层。"""
from db import get_conn


def create(username: str, password_hash: str, role: str = "employee") -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_by_name(username: str):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()


def get(uid: int):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (uid,)
        ).fetchone()
    finally:
        conn.close()
