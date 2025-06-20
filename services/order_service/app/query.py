from sqlalchemy.orm import Session
import requests
from fastapi import HTTPException
import pika
import json

from . import models, schemas

USER_SERVICE_URL = "http://localhost:8001/users"
PRODUCT_SERVICE_URL = "http://localhost:8004/products"


def create_order(db: Session, order: schemas.OrderCreate):

    # check user is exist
    user_response = requests.get(f"{USER_SERVICE_URL}/{order.user_id}")
    if user_response.status_code != 200:
        raise HTTPException(
            status_code=404, detail=f"User with id {order.user_id} not found"
        )

    total_amount = 0
    order_items_to_create = []

    for item in order.items:
        product_response = requests.get(f"{PRODUCT_SERVICE_URL}/{item.product_id}")
        if product_response.status_code != 200:
            raise HTTPException(
                status_code=404, detail=f"Product with id {item.product_id} not found"
            )

        product_data = product_response.json()

        if product_data["stock_quantity"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product {item.product_id}",
            )

        price = product_data["price"]
        total_amount += price * item.quantity

        order_items_to_create.append(
            models.OrderItem(
                product_id=item.product_id, quantity=item.quantity, price_per_item=price
            )
        )

    db_order = models.Order(user_id=order.user_id, total_amount=total_amount)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for item_to_create in order_items_to_create:
        item_to_create.order_id = db_order.id
        db.add(item_to_create)

    db.commit()
    db.refresh(db_order)

    # --- send message to RABBITMQ ---
    try:
        user_data = user_response.json()
        user_email = user_data.get("email")

        message = {
            "order_id": db_order.id,
            "user_id": db_order.user_id,
            "user_email": user_email,
            "total_amount": db_order.total_amount,
        }

        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()
        channel.queue_declare(
            queue="order_notifications", durable=True
        )  # Đảm bảo queue tồn tại
        channel.basic_publish(
            exchange="",
            routing_key="order_notifications",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )
        connection.close()
        print(f" [x] Sent 'Order Created' message for order {db_order.id}")
    except Exception as e:
        print(f" [!] Failed to send message to RabbitMQ: {e}")
    return db_order
