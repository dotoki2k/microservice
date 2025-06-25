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


def update_stock_quantity(db: Session, product_info: dict):
    if not product_info:
        return []
    product_ids = list(product_info.keys())

    try:
        db_products = (
            db.query(models.Product)
            .filter(models.Product.id.in_(product_ids))
            .with_for_update()
            .all()
        )

        product_map = {str(p.id): p for p in db_products}
        if len(db_products) != len(product_ids):
            found_ids = set(product_map.keys())
            missing_ids = [pid for pid in product_ids if pid not in found_ids]
            raise HTTPException(
                status_code=404,
                detail=f"The following product IDs were not found: {', '.join(missing_ids)}",
            )

        for product_id, required_quantity in product_info.items():
            db_product = product_map[product_id]
            if db_product.stock_quantity < required_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for product '{db_product.name}'. "
                    f"Available: {db_product.stock_quantity}, Required: {required_quantity}",
                )

        for product_id, quantity_to_subtract in product_info.items():
            product_map[product_id].stock_quantity -= quantity_to_subtract

        db.commit()
        return db_products

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )
