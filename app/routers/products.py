"""
Product management endpoints (UC09 - Register product, UC13 - Approve product)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user
from ..utils.image_handler import save_image, get_image_url, validate_image_file

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
    db_product = crud.create_product(db=db, product=product, user_id=current_user.accountID)
    
    # Parse additional_images JSON string back to list
    additional_images_list = None
    if db_product.additionalImages:
        import json
        try:
            additional_images_list = json.loads(db_product.additionalImages)
        except:
            additional_images_list = None
    
    return schemas.Product(
        productID=db_product.productID,
        productName=db_product.productName,
        productDescription=db_product.productDescription,
        productType=db_product.productType,
        imageUrl=db_product.imageUrl,
        additionalImages=additional_images_list,
        shippingStatus=db_product.shippingStatus,
        approvalStatus=db_product.approvalStatus,
        rejectionReason=db_product.rejectionReason,
        suggestedByUserID=db_product.suggestedByUserID,
        createdAt=db_product.createdAt,
        updatedAt=db_product.updatedAt
    )


@router.post("/register-with-images", response_model=schemas.Product)
async def register_product_with_images(
    product_name: str = Form(...),
    product_description: str = Form(...),
    product_type: str = Form(...),
    main_image: Optional[UploadFile] = File(None),
    additional_images: Optional[List[UploadFile]] = File(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register product for auction with image uploads (UC09)
    
    POST /products/register-with-images
    Headers: Authorization: Bearer <access_token>
    Form Data:
    - product_name: Product name
    - product_description: Product description  
    - product_type: Product type
    - main_image: Main product image (optional)
    - additional_images: Additional product images (max 4, optional)
    
    Returns: Created product information with local image paths
    """
    # First create product without images
    product_data = schemas.ProductCreate(
        product_name=product_name,
        product_description=product_description,
        product_type=product_type
    )
    
    db_product = crud.create_product(db=db, product=product_data, user_id=current_user.accountID)
    
    # Process main image
    main_image_path = None
    if main_image:
        try:
            # Validate main image
            file_content = await main_image.read()
            is_valid, error_message = validate_image_file(file_content)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Main image error: {error_message}")
            
            # Save main image with product ID
            main_image_path = save_image(file_content, main_image.filename, db_product.productID)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to save main image: {str(e)}")
    
    # Process additional images
    additional_images_paths = []
    if additional_images:
        for i, image in enumerate(additional_images[:4]):  # Max 4 additional images
            try:
                # Validate image
                file_content = await image.read()
                is_valid, error_message = validate_image_file(file_content)
                if not is_valid:
                    continue  # Skip invalid images
                
                # Save additional image
                image_path = save_image(file_content, image.filename, db_product.productID)
                additional_images_paths.append(image_path)
                
            except Exception as e:
                # Log error but continue processing other images
                print(f"Failed to save additional image {i}: {str(e)}")
                continue
    
    # Update product with image paths
    try:
        # Update main image URL if provided
        if main_image_path:
            db_product.imageUrl = main_image_path
        
        # Update additional images if any
        if additional_images_paths:
            db_product.additionalImages = json.dumps(additional_images_paths)
        
        db.commit()
        db.refresh(db_product)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update product with images: {str(e)}")
    
    # Return product with image URLs
    additional_images_list = None
    if db_product.additionalImages:
        try:
            additional_images_list = json.loads(db_product.additionalImages)
        except:
            additional_images_list = None
    
    return schemas.Product(
        productID=db_product.productID,
        productName=db_product.productName,
        productDescription=db_product.productDescription,
        productType=db_product.productType,
        imageUrl=db_product.imageUrl,
        additionalImages=additional_images_list,
        shippingStatus=db_product.shippingStatus,
        approvalStatus=db_product.approvalStatus,
        rejectionReason=db_product.rejectionReason,
        suggestedByUserID=db_product.suggestedByUserID,
        createdAt=db_product.createdAt,
        updatedAt=db_product.updatedAt
    )


@router.get("/", response_model=list[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all products
    
    GET /products?skip=0&limit=100
    Returns: List of products
    """
    products = crud.get_products(db=db, skip=skip, limit=limit)
    
    # Parse additionalImages JSON string back to list for each product
    parsed_products = []
    for product in products:
        additional_images_list = None
        if product.additionalImages:
            try:
                additional_images_list = json.loads(product.additionalImages)
            except:
                additional_images_list = None
        
        parsed_products.append(schemas.Product(
            productID=product.productID,
            productName=product.productName,
            productDescription=product.productDescription,
            productType=product.productType,
            imageUrl=product.imageUrl,
            additionalImages=additional_images_list,
            shippingStatus=product.shippingStatus,
            approvalStatus=product.approvalStatus,
            rejectionReason=product.rejectionReason,
            suggestedByUserID=product.suggestedByUserID,
            createdAt=product.createdAt,
            updatedAt=product.updatedAt
        ))
    
    return parsed_products


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
    
    # Parse additionalImages JSON string back to list
    additional_images_list = None
    if product.additionalImages:
        import json
        try:
            additional_images_list = json.loads(product.additionalImages)
        except:
            additional_images_list = None
    
    return schemas.Product(
        productID=product.productID,
        productName=product.productName,
        productDescription=product.productDescription,
        productType=product.productType,
        imageUrl=product.imageUrl,
        additionalImages=additional_images_list,
        shippingStatus=product.shippingStatus,
        createdAt=product.createdAt,
        updatedAt=product.updatedAt
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
    
    # Parse additionalImages JSON string back to list
    additional_images_list = None
    if updated_product.additionalImages:
        import json
        try:
            additional_images_list = json.loads(updated_product.additionalImages)
        except:
            additional_images_list = None
    
    return schemas.Product(
        productID=updated_product.productID,
        productName=updated_product.productName,
        productDescription=updated_product.productDescription,
        productType=updated_product.productType,
        imageUrl=updated_product.imageUrl,
        additionalImages=additional_images_list,
        shippingStatus=updated_product.shippingStatus,
        createdAt=updated_product.createdAt,
        updatedAt=updated_product.updatedAt
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
    return [p for p in products if p.approvalStatus == "pending"]


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