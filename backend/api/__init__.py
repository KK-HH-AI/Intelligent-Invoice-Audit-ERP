"""API 网关层：路由注册 + HTTP 依赖注入（deps）。

纪律：
- 端点只做"HTTP ↔ 服务层"翻译：解析请求、调用 service、返回 JSON/状态码；
- 不写业务逻辑、不写 SQL、不直接调 DeepSeek/PaddleOCR；
- 鉴权插销统一放 deps.py，端点通过 Depends 引用。
"""
