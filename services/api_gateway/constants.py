SERVICES = {
    "api/users": "http://localhost:8001",
    "api/products": "http://localhost:8002",
    "api/orders": "http://localhost:8003",
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
