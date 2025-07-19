import threading
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from typing import List

from shared.logger.logger import get_logger
from . import query, models, schemas
from .database import engine, get_db
from .consumer import run_kafka_consumer

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
kafka_threads = []
stop_event = threading.Event()
logger = get_logger("Product_service")


@app.on_event("startup")
def startup_event():
    print("The product service is initiating ...")
    num_consumers = 2
    for i in range(num_consumers):
        consumer_id = f"Consumer-{i}"
        thread = threading.Thread(
            target=run_kafka_consumer, args=(consumer_id, stop_event)
        )
        kafka_threads.append(thread)
        thread.start()


@app.on_event("shutdown")
def shutdown_event():
    print("The product service is shutting down")
    stop_event.set()
    for thread in kafka_threads:
        thread.join()


@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        db = query.create_product(db=db, product=product)
        logger.debug(f"The product ({product}) created.")
        return db
    except Exception as ex:
        logger.exception(
            f"An error occurred while create a product ({product}). The error: {str(ex)}."
        )
        return None


@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = query.get_products(db, skip=skip, limit=limit)
    return products


@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = query.get_product(db, product_id=product_id)
    if db_product is None:
        logger.debug(f"The product [id={product_id}] not found in the database.")
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@app.patch("/products/", response_model=List[schemas.Product])
def update_quantity_product(product_info: dict, db: Session = Depends(get_db)):
    db_product = query.update_stock_quantity(db, product_info)
    if db_product is None:
        logger.debug(f"The product ({str(product_info)}) not found in the database.")
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product
