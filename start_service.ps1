Start-Process powershell -ArgumentList "uvicorn services.user_service.app.main:app --reload --port 8001"
Start-Process powershell -ArgumentList "uvicorn services.product_service.app.main:app --reload --port 8002"
Start-Process powershell -ArgumentList "uvicorn services.order_service.app.main:app --reload --port 8003"
Start-Process powershell -ArgumentList "uvicorn services.api_gateway.gateway:app --reload --port 8000"
