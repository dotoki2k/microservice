import httpx

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .schemas import UserLogin
from .constants import (
    SERVICES,
    PUBLIC_ROUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    RATE_LIMITED,
)

# init Limiter
limiter = Limiter(key_func=get_remote_address)


# Middleware để kiểm tra JWT
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path  # '/api/products/'
        is_public_route = False
        method = request.method
        for key in PUBLIC_ROUTES.keys():
            if path.startswith(key):
                if method in PUBLIC_ROUTES.get(key, []):
                    is_public_route = True
                break

        if is_public_route:
            response = await call_next(request)
            return response
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response("Unauthorized: Missing or invalid token", status_code=401)

        token = auth_header.split(" ")[1]

        try:
            jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except JWTError:
            # Token is not valid (wrong signature, expired,...)
            return Response("Unauthorized: Invalid token", status_code=401)

        response = await call_next(request)
        return response


app = FastAPI()
app.add_middleware(AuthMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# create only a HTTP client
# best practice to improve performance
client = httpx.AsyncClient()


@app.post("/api/login")
@limiter.limit(RATE_LIMITED)
async def login(request: Request, form_data: UserLogin):
    try:
        # call to user_service to authen
        response = await client.post(
            "http://127.0.0.1:8001/token",
            json={"username": form_data.username, "password": form_data.password},
        )
        response.raise_for_status()
        token = response.json()
        return token

    except httpx.HTTPStatusError as exc:
        return JSONResponse(
            status_code=exc.response.status_code, content=exc.response.json()
        )


# @app.post("/api/logout")
# async def logout(current_user: dict = Depends(get_current_user)):
#     jti = current_user.get("jti")
#     exp = current_user.get("exp")

#     # Thêm JTI của token vào blocklist trong Redis
#     # Set TTL (thời gian sống) cho key bằng đúng thời gian còn lại của token
#     # để Redis tự động dọn dẹp
#     time_to_expire = int(exp - time.time())
#     if time_to_expire > 0:
#         redis_client.setex(f"jti:{jti}", time_to_expire, "logged_out")

#     return {"message": "Successfully logged out"}


# --- Route handle all requests ---
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit(RATE_LIMITED)
async def catch_all(request: Request, full_path: str):
    target_url = None

    # mapping services
    split_path = full_path.strip("/").split("/")  # full_path = 'api/users/token'
    key_path = "/".join(split_path[0:2])
    service_url = SERVICES.get(key_path, None)
    if service_url:
        service_path = "/".join(split_path[1:])
        target_url = f"{service_url}/{service_path}"
    if not target_url:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    params = request.query_params
    # send request to service.
    try:
        rp_req = client.build_request(
            method=method, url=target_url, headers=headers, content=body, params=params
        )
        rp_resp = await client.send(rp_req)
        return StreamingResponse(
            rp_resp.aiter_bytes(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
            background=rp_resp.aclose,
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
