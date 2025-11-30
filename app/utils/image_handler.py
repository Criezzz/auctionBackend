"""
Image handling utilities for local storage
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import io

# Base storage path
STORAGE_BASE = Path("storage")
IMAGES_PATH = STORAGE_BASE / "images" / "products"

# Create directories if they don't exist
IMAGES_PATH.mkdir(parents=True, exist_ok=True)

def save_image(file_content: bytes, original_filename: str, product_id: Optional[int] = None) -> str:
    """
    Save uploaded image to local storage
    
    Args:
        file_content: Raw image bytes
        original_filename: Original filename for extension
        product_id: Product ID for organized storage (optional)
    
    Returns:
        str: Relative path to saved image
    """
    # Generate unique filename
    file_extension = Path(original_filename).suffix.lower()
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # Determine storage path
    if product_id:
        # Create product-specific subdirectory
        product_dir = IMAGES_PATH / f"product_{product_id}"
        product_dir.mkdir(exist_ok=True)
        storage_path = product_dir / unique_filename
    else:
        # Store in general products directory
        storage_path = IMAGES_PATH / unique_filename
    
    # Validate and save image
    try:
        # Verify it's a valid image
        image = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if image.mode in ("RGBA", "P"):
            # Create white background for transparency
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = rgb_image
        
        # Save image
        image.save(storage_path, "JPEG", quality=85, optimize=True)
        
        # Return relative path
        if product_id:
            return f"storage/images/products/product_{product_id}/{unique_filename}"
        else:
            return f"storage/images/products/{unique_filename}"
            
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")

def delete_image(image_path: str) -> bool:
    """
    Delete image from local storage
    
    Args:
        image_path: Relative path to image
    
    Returns:
        bool: True if deleted successfully
    """
    try:
        full_path = Path(image_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception:
        return False

def get_image_url(image_path: str, base_url: str = "http://localhost:8000") -> str:
    """
    Generate full URL for accessing image
    
    Args:
        image_path: Relative path to image
        base_url: Base URL of the application
    
    Returns:
        str: Full URL to access the image
    """
    if image_path.startswith("http"):
        return image_path
    
    # Convert storage path to static file path
    static_path = image_path.replace("storage/", "static/")
    return f"{base_url}/{static_path}"

def validate_image_file(file_content: bytes, max_size_mb: int = 5) -> Tuple[bool, str]:
    """
    Validate uploaded image file
    
    Args:
        file_content: Raw image bytes
        max_size_mb: Maximum file size in MB
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check file size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
    
    # Check if it's a valid image
    try:
        image = Image.open(io.BytesIO(file_content))
        image.verify()  # Verify it's not corrupted
        return True, ""
    except Exception:
        return False, "File is not a valid image"

def get_supported_formats() -> List[str]:
    """Get list of supported image formats"""
    return ["JPEG", "JPG", "PNG", "WEBP"]

def create_sample_images():
    """Create sample images for demo purposes"""
    # Create a simple colored rectangle image for demo
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create sample images directory
        sample_dir = IMAGES_PATH / "samples"
        sample_dir.mkdir(exist_ok=True)
        
        # Create 3 sample images
        colors = [
            ("#FF6B6B", "Sample Product 1"),
            ("#4ECDC4", "Sample Product 2"), 
            ("#45B7D1", "Sample Product 3")
        ]
        
        for i, (color, title) in enumerate(colors, 1):
            # Create image
            img = Image.new("RGB", (400, 300), color)
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                # Try to use a font, fallback to default if not available
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), title, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (400 - text_width) // 2
                y = (300 - text_height) // 2
                draw.text((x, y), title, fill="white", font=font)
            except:
                draw.text((150, 140), title, fill="white")
            
            # Save image
            img.save(sample_dir / f"sample_{i}.jpg", "JPEG", quality=85)
            
        print("Sample images created successfully!")
        
    except ImportError:
        print("PIL not available, skipping sample image creation")
    except Exception as e:
        print(f"Error creating sample images: {e}")

if __name__ == "__main__":
    create_sample_images()