import httpx
import asyncio
import requests

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import query, models, schemas
from .database import engine, get_db
from shared import utils
from shared.kafka_producer.producer import send_message_to_kafka_server

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

USER_SERVICE_URL = "http://127.0.0.1:8001/users"
PRODUCT_SERVICE_URL = "http://127.0.0.1:8002/products"
PRODUCT_TOPIC = "product_topic"


@app.post("/orders/", response_model=schemas.Order)
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        # check user is existed
        async with httpx.AsyncClient() as client:
            user_task = client.get(f"{USER_SERVICE_URL}/{order.user_id}")
            product_tasks = [
                client.get(f"{PRODUCT_SERVICE_URL}/{item.product_id}")
                for item in order.items
            ]
            results = await asyncio.gather(
                user_task, *product_tasks, return_exceptions=True
            )
            user_response = results[0]
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=404, detail=f"User with id {order.user_id} not found"
                )

            product_responses = results[1:]
            order_items_to_create = []
            product_update_quantity = {}
            for i, product_response in enumerate(product_responses):
                item = order.items[i]
                print("order: ", order)
                if product_update_quantity.get(item.product_id, None) is None:
                    product_update_quantity[item.product_id] = item.quantity
                else:
                    product_update_quantity[item.product_id] = (
                        product_update_quantity.get(item.product_id, 0) + item.quantity
                    )

                product_response = requests.get(
                    f"{PRODUCT_SERVICE_URL}/{item.product_id}"
                )
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
        if order_items_to_create:
            db_order = query.create_order(
                db=db, order=order, order_items=order_items_to_create
            )

        # send notification
        if db_order:
            send_message_to_kafka_server(PRODUCT_TOPIC, product_update_quantity)

            user_data = user_response.json()
            user_email = user_data.get("email")
            message = {
                "order_id": db_order.id,
                "user_id": db_order.user_id,
                "user_email": user_email,
                "total_amount": db_order.total_amount,
            }
            utils.send_message_to_rabitmq_sever(message, "order_notifications")
        return db_order
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@app.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    try:
        return query.get_order_by_id(db=db, order_id=order_id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An internal error occurred")
