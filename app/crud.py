from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas
from .auth import get_password_hash, verify_password


# ========== ITEM CRUD ========== #
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(title=item.title, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# ========== ACCOUNT CRUD ========== #
def get_account_by_username(db: Session, username: str) -> models.Account | None:
    """Get account by username"""
    return db.query(models.Account).filter(models.Account.username == username).first()


def get_account_by_id(db: Session, account_id: int) -> models.Account | None:
    """Get account by ID"""
    return db.query(models.Account).filter(models.Account.account_id == account_id).first()


def create_account(db: Session, account: schemas.AccountCreate) -> models.Account:
    """Create new account with hashed password"""
    hashed_password = get_password_hash(account.password)
    db_account = models.Account(
        username=account.username,
        email=account.email,
        password=hashed_password,
        first_name=account.first_name,
        last_name=account.last_name,
        phone_num=account.phone_num,
        created_at=datetime.utcnow(),
        activated=True,  # Auto-activate for demo; in production, send email verification
        is_admin=False,
        is_authenticated=False
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def authenticate_account(db: Session, username: str, password: str) -> models.Account | None:
    """Authenticate account with username and password"""
    account = get_account_by_username(db, username)
    if not account:
        return None
    if not verify_password(password, account.password):
        return None
    return account

