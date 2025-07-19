from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm

from shared.logger.logger import get_logger
from . import query, models, schemas
from .database import engine, get_db
from .auth import verify_password, create_access_token
from .config import ACCESS_TOKEN_EXPIRE_MINUTES

# init database
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
logger = get_logger("User service")


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create new user"""
    db_user = query.get_user_by_username(db, username=user.username)
    if db_user:
        logger.debug(f"The user ({str(user)}) already exsited.")
        raise HTTPException(status_code=400, detail="username already registered")
    return query.create_user(db=db, user=user)


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by user id"""
    db_user = query.get_user(db, user_id=user_id)
    if db_user is None:
        logger.debug(f"The user [{user_id}] not found.")
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: schemas.UserLogin, db: Session = Depends(get_db)
):
    user = query.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.debug("The username or password is incorrect.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.debug(
        f"Generate the token for the user [{form_data.username}] successfully."
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
def read_root():
    return {"Project": "Microservice Learning", "Service": "User Service"}
