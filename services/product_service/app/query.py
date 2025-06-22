from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()


def update_stock_quantity(db: Session, product_id: int, quantities_decreased: int):
    db_products = (
        db.query(models.Product).filter(models.Product.id == product_id).first()
    )
    if not db_products:
        raise HTTPException(
            status_code=404, detail=f"Product with id {product_id} not found"
        )

    if db_products.stock_quantity < quantities_decreased:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough stock for product {db_products.name}. Available: {db_products.stock_quantity}, Required: {quantities_decreased}",
        )
    db_products.stock_quantity -= quantities_decreased
    db.commit()
    return db_products
