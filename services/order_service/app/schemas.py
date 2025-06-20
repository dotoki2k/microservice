from pydantic import BaseModel
from typing import List
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]


class OrderItem(OrderItemCreate):
    id: int
    price_per_item: float

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    user_id: int
    total_amount: float
    created_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True
