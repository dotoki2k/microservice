SERVICES = {
    "api/users": "http://127.0.0.1:8001",
    "api/products": "http://127.0.0.1:8002",
    "api/orders": "http://127.0.0.1:8003",
}

PUBLIC_ROUTES = {
    "/api/users/token": ["GET"],
    "/api/users/": ["GET"],
    "/api/products/": ["GET"],
    "/docs": ["GET"],
    "/api/login": ["POST"],
    "/": ["GET"],
}

JWT_SECRET_KEY = "the_default_secret_key"
JWT_ALGORITHM = "HS256"
RATE_LIMITED = "5/minute"
