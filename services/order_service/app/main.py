import requests
import time
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import query, models, schemas
from .database import engine, get_db
from shared import utils

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

USER_SERVICE_URL = "http://localhost:8001/users"
PRODUCT_SERVICE_URL = "http://localhost:8002/products"


@app.post("/orders/", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        start_time = time.time()
        print(f"[OrderService] --- Bắt đầu xử lý order ---")
        # check user is exist
        user_check_start = time.time()
        user_response = requests.get(f"{USER_SERVICE_URL}/{order.user_id}")
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=404, detail=f"User with id {order.user_id} not found"
            )
        print(
            f"[OrderService] Gọi UserService mất: {time.time() - user_check_start:.4f} giây"
        )
        # check products
        order_items_to_create = []
        product_check_start = time.time()
        product_update_quantity = {}
        for item in order.items:
            product_update_quantity[item.product_id] = item.quantity
            product_response = requests.get(f"{PRODUCT_SERVICE_URL}/{item.product_id}")
            if product_response.status_code != 200:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with id {item.product_id} not found",
                )

            product_data = product_response.json()

            if product_data["stock_quantity"] < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for product {item.product_id}",
                )

            price = product_data["price"]
            order_items_to_create.append(
                models.OrderItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_per_item=price,
                )
            )
        db_order = None
        print(
            f"[OrderService] Gọi ProductService (tuần tự) mất: {time.time() - product_check_start:.4f} giây"
        )
        db_write_start = time.time()
        if order_items_to_create:
            db_order = query.create_order(
                db=db, order=order, order_items=order_items_to_create
            )

        # send notification
        if db_order:
            product_response = requests.patch(
                f"{PRODUCT_SERVICE_URL}/", json=product_update_quantity
            )
            if product_response.status_code != 200:
                raise HTTPException(
                    status_code=404,
                    detail=f"Update quantity for products id [{item.product_id}] failed.",
                )
            # user_data = user_response.json()
            # user_email = user_data.get("email")

            # message = {
            #     "order_id": db_order.id,
            #     "user_id": db_order.user_id,
            #     "user_email": user_email,
            #     "total_amount": db_order.total_amount,
            # }
            # utils.send_message_to_rabitmq_sever(message, "order_notifications")
        print(
            f"[OrderService] Ghi vào Database mất: {time.time() - db_write_start:.4f} giây"
        )
        print(
            f"[OrderService] >>> Tổng thời gian xử lý: {time.time() - start_time:.4f} giây <<<"
        )
        return db_order
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@app.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        return query.create_order(db=db, order=order)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An internal error occurred")
