"""
Product management endpoints (UC09 - Register product, UC13 - Approve product)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.Product)
def register_product(
    product: schemas.ProductCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register product for auction (UC09)
    
    POST /products/register
    Headers: Authorization: Bearer <access_token>
    Body: { "product_name": "Figure Name", "product_description": "...", "product_type": "..." }
    Returns: Created product information
    """
    # Create product
    db_product = crud.create_product(db=db, product=product, user_id=current_user.account_id)
    
    return schemas.Product(
        product_id=db_product.product_id,
        product_name=db_product.product_name,
        product_description=db_product.product_description,
        product_type=db_product.product_type,
        shipping_status=db_product.shipping_status,
        approval_status=db_product.approval_status,
        rejection_reason=db_product.rejection_reason,
        suggested_by_user_id=db_product.suggested_by_user_id,
        created_at=db_product.created_at,
        updated_at=db_product.updated_at
    )


@router.get("/", response_model=list[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all products
    
    GET /products?skip=0&limit=100
    Returns: List of products
    """
    products = crud.get_products(db=db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get product by ID
    
    GET /products/{product_id}
    Returns: Product information
    """
    product = crud.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return schemas.Product(
        product_id=product.product_id,
        product_name=product.product_name,
        product_description=product.product_description,
        product_type=product.product_type,
        shipping_status=product.shipping_status,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update product information (Admin only)
    
    PUT /products/{product_id}
    Headers: Authorization: Bearer <access_token>
    Body: { "product_name": "...", "shipping_status": "..." }
    Returns: Updated product information
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Update product
    updated_product = crud.update_product(db=db, product_id=product_id, product_update=product_update)
    
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return schemas.Product(
        product_id=updated_product.product_id,
        product_name=updated_product.product_name,
        product_description=updated_product.product_description,
        product_type=updated_product.product_type,
        shipping_status=updated_product.shipping_status,
        created_at=updated_product.created_at,
        updated_at=updated_product.updated_at
    )


@router.delete("/{product_id}", response_model=schemas.MessageResponse)
def delete_product(
    product_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete product (Admin only)
    
    DELETE /products/{product_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Delete product
    success = crud.delete_product(db=db, product_id=product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return schemas.MessageResponse(message="Product deleted successfully")


@router.get("/pending/approval", response_model=list[schemas.Product])
def get_pending_products(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get products pending approval (Admin only - UC13)
    
    GET /products/pending/approval
    Headers: Authorization: Bearer <access_token>
    Returns: List of products pending approval
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get products with "pending" approval status
    products = crud.get_products(db=db, skip=0, limit=100)
    return [p for p in products if p.approval_status == "pending"]


@router.post("/{product_id}/approve", response_model=schemas.MessageResponse)
def approve_product(
    product_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve product for auction (Admin only - UC13)
    
    POST /products/{product_id}/approve
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Update product status to "approved"
    product_update = schemas.ProductUpdate(
        approval_status="approved",
        shipping_status="approved"
    )
    updated_product = crud.update_product(db=db, product_id=product_id, product_update=product_update)
    
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return schemas.MessageResponse(message="Product approved successfully")


@router.post("/{product_id}/reject", response_model=schemas.MessageResponse)
def reject_product(
    product_id: int,
    reject_request: schemas.ProductRejectRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject product with reason (Admin only)
    
    POST /products/{product_id}/reject
    Headers: Authorization: Bearer <access_token>
    Body: { "rejection_reason": "Product does not meet quality standards" }
    Returns: Success message
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Update product status to "rejected" with reason
    product_update = schemas.ProductUpdate(
        approval_status="rejected",
        shipping_status="rejected",
        rejection_reason=reject_request.rejection_reason
    )
    updated_product = crud.update_product(db=db, product_id=product_id, product_update=product_update)
    
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return schemas.MessageResponse(message="Product rejected")