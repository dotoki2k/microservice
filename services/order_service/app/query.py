from sqlalchemy.orm import Session
from typing import List
from . import models, schemas


def create_order(
    db: Session, order: schemas.OrderCreate, order_items: List[models.OrderItem]
):

    db_order = models.Order(user_id=order.user_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    total_amount = 0
    for item_to_create in order_items:
        item_to_create.order_id = db_order.id
        total_amount += item_to_create.price_per_item * item_to_create.quantity
        db.add(item_to_create)

    db_order.total_amount = total_amount
    db.commit()
    db.refresh(db_order)
    return db_order


def get_order_by_id(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()
