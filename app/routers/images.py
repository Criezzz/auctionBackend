"""
Image upload and management router for local storage
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from pathlib import Path

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user
from ..utils.image_handler import (
    save_image, 
    delete_image, 
    get_image_url, 
    validate_image_file,
    get_supported_formats,
    IMAGES_PATH
)

router = APIRouter(prefix="/images", tags=["Image Management"])

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    product_id: Optional[int] = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload image to local storage
    
    POST /images/upload
    Form Data:
    - file: Image file (JPEG, PNG, WEBP)
    - product_id: Optional product ID for organization
    
    Returns: Uploaded image information with local path
    """
    # Validate file
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    # Validate file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(get_supported_formats())}"
        )
    
    # Read and validate file content
    file_content = await file.read()
    is_valid, error_message = validate_image_file(file_content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Save image
    try:
        image_path = save_image(file_content, file.filename, product_id)
        image_url = get_image_url(image_path)
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "image_path": image_path,
            "image_url": image_url,
            "filename": file.filename,
            "size_bytes": len(file_content),
            "product_id": product_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {str(e)}"
        )

@router.post("/upload/multiple")
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    product_id: Optional[int] = Form(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload multiple images to local storage
    
    POST /images/upload/multiple
    Form Data:
    - files: List of image files (max 5)
    - product_id: Optional product ID for organization
    
    Returns: List of uploaded images with their information
    """
    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 images allowed per upload"
        )
    
    uploaded_images = []
    
    for file in files:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            continue  # Skip invalid files
        
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            continue  # Skip unsupported files
        
        # Read and validate file content
        try:
            file_content = await file.read()
            is_valid, error_message = validate_image_file(file_content)
            if not is_valid:
                continue  # Skip invalid files
            
            # Save image
            image_path = save_image(file_content, file.filename, product_id)
            image_url = get_image_url(image_path)
            
            uploaded_images.append({
                "filename": file.filename,
                "image_path": image_path,
                "image_url": image_url,
                "size_bytes": len(file_content),
                "success": True
            })
            
        except Exception as e:
            uploaded_images.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    if not uploaded_images:
        raise HTTPException(
            status_code=400,
            detail="No valid images uploaded"
        )
    
    return {
        "success": True,
        "message": f"Uploaded {len([img for img in uploaded_images if img.get('success')])} images",
        "images": uploaded_images,
        "total_uploaded": len([img for img in uploaded_images if img.get('success')]),
        "total_failed": len([img for img in uploaded_images if not img.get('success')])
    }

@router.delete("/delete")
async def delete_uploaded_image(
    image_path: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete image from local storage
    
    DELETE /images/delete?image_path=storage/images/products/sample.jpg
    Query Parameters:
    - image_path: Relative path to image to delete
    
    Returns: Success message
    """
    if not image_path.startswith("storage/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid image path"
        )
    
    success = delete_image(image_path)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Image not found or could not be deleted"
        )
    
    return {
        "success": True,
        "message": "Image deleted successfully",
        "deleted_path": image_path
    }

@router.get("/view/{image_path:path}")
async def view_image(image_path: str):
    """
    Serve image files from local storage
    
    GET /images/view/storage/images/products/sample.jpg
    
    Returns: Image file
    """
    # Security: prevent directory traversal
    if ".." in image_path or image_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid image path")
    
    # Check if file exists
    full_path = Path(image_path)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    content_type = "image/jpeg"  # Default
    if image_path.lower().endswith('.png'):
        content_type = "image/png"
    elif image_path.lower().endswith('.webp'):
        content_type = "image/webp"
    
    return FileResponse(
        path=image_path,
        media_type=content_type
    )

@router.get("/list")
async def list_images(
    product_id: Optional[int] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List images in storage
    
    GET /images/list?product_id=123
    Query Parameters:
    - product_id: Optional filter by product ID
    
    Returns: List of images with their information
    """
    images = []
    
    if product_id:
        # List images for specific product
        product_dir = IMAGES_PATH / f"product_{product_id}"
        if product_dir.exists():
            for image_file in product_dir.glob("*"):
                if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    relative_path = f"storage/images/products/product_{product_id}/{image_file.name}"
                    images.append({
                        "filename": image_file.name,
                        "image_path": relative_path,
                        "image_url": get_image_url(relative_path),
                        "size_bytes": image_file.stat().st_size,
                        "modified_time": image_file.stat().st_mtime
                    })
    else:
        # List all images
        for image_file in IMAGES_PATH.rglob("*"):
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                # Skip sample images
                if "samples" in str(image_file):
                    continue
                
                relative_path = str(image_file.relative_to("."))
                images.append({
                    "filename": image_file.name,
                    "image_path": relative_path,
                    "image_url": get_image_url(relative_path),
                    "size_bytes": image_file.stat().st_size,
                    "modified_time": image_file.stat().st_mtime
                })
    
    return {
        "success": True,
        "images": images,
        "total_count": len(images),
        "storage_path": str(IMAGES_PATH)
    }

@router.get("/formats")
async def get_supported_image_formats():
    """
    Get supported image formats
    
    GET /images/formats
    
    Returns: List of supported formats and limits
    """
    return {
        "supported_formats": get_supported_formats(),
        "max_file_size_mb": 5,
        "max_files_per_request": 5,
        "features": [
            "Automatic JPEG conversion for transparency",
            "Image optimization and compression",
            "Unique filename generation",
            "Product-specific organization"
        ]
    }

@router.post("/samples")
async def create_sample_images(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create sample images for demo purposes (Admin only)
    
    POST /images/samples
    
    Returns: Sample images creation result
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from ..utils.image_handler import create_sample_images
    
    try:
        create_sample_images()
        return {
            "success": True,
            "message": "Sample images created successfully",
            "samples_location": "storage/images/products/samples/"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create sample images: {str(e)}"
        )