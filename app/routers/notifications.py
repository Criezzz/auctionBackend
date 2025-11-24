"""
Notification management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=list[schemas.Notification])
def get_notifications(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notifications
    
    GET /notifications?skip=0&limit=50
    Headers: Authorization: Bearer <access_token>
    Returns: List of notifications
    """
    notifications = crud.get_notifications_by_user(db, current_user.account_id, skip=skip, limit=limit)
    return notifications


@router.get("/unread", response_model=list[schemas.Notification])
def get_unread_notifications(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get unread notifications
    
    GET /notifications/unread?skip=0&limit=50
    Headers: Authorization: Bearer <access_token>
    Returns: List of unread notifications
    """
    notifications = crud.get_unread_notifications_by_user(db, current_user.account_id, skip=skip, limit=limit)
    return notifications


@router.get("/unread/count", response_model=dict)
def get_unread_count(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get count of unread notifications
    
    GET /notifications/unread/count
    Headers: Authorization: Bearer <access_token>
    Returns: { "count": 5 }
    """
    count = crud.get_unread_count(db, current_user.account_id)
    return {"count": count}


@router.put("/{notification_id}/read", response_model=schemas.Notification)
def mark_notification_read(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notification as read
    
    PUT /notifications/{notification_id}/read
    Headers: Authorization: Bearer <access_token>
    Returns: Updated notification
    """
    # Get notification
    notification = crud.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Check if user owns the notification
    if notification.user_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own notifications as read"
        )
    
    # Mark as read
    updated_notification = crud.update_notification_status(db, notification_id, is_read=True)
    if not updated_notification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to mark notification as read"
        )
    
    return schemas.Notification(
        notification_id=updated_notification.notification_id,
        user_id=updated_notification.user_id,
        auction_id=updated_notification.auction_id,
        notification_type=updated_notification.notification_type,
        title=updated_notification.title,
        message=updated_notification.message,
        is_read=updated_notification.is_read,
        is_sent=updated_notification.is_sent,
        created_at=updated_notification.created_at,
        read_at=updated_notification.read_at
    )


@router.put("/mark-all-read", response_model=schemas.MessageResponse)
def mark_all_read(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications as read
    
    PUT /notifications/mark-all-read
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    success = crud.mark_all_notifications_read(db, current_user.account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to mark all notifications as read"
        )
    
    return schemas.MessageResponse(message="All notifications marked as read")


@router.delete("/{notification_id}", response_model=schemas.MessageResponse)
def delete_notification(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete notification
    
    DELETE /notifications/{notification_id}
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    # Get notification
    notification = crud.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Check if user owns the notification
    if notification.user_id != current_user.account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notifications"
        )
    
    # Delete notification
    success = crud.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete notification"
        )
    
    return schemas.MessageResponse(message="Notification deleted successfully")


@router.get("/auction/{auction_id}", response_model=list[schemas.Notification])
def get_auction_notifications(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications related to specific auction
    
    GET /notifications/auction/{auction_id}
    Headers: Authorization: Bearer <access_token>
    Returns: List of auction-related notifications
    """
    # Verify auction exists
    auction = crud.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Get all user notifications for this auction
    all_notifications = crud.get_notifications_by_user(db, current_user.account_id, skip=0, limit=1000)
    auction_notifications = [n for n in all_notifications if n.auction_id == auction_id]
    
    return auction_notifications


@router.post("/test", response_model=schemas.MessageResponse)
def create_test_notification(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a test notification (for testing purposes)
    
    POST /notifications/test
    Headers: Authorization: Bearer <access_token>
    Returns: Success message
    """
    notification_data = schemas.NotificationCreate(
        user_id=current_user.account_id,
        auction_id=1,  # Test auction ID
        notification_type="test",
        title="Test Notification",
        message="This is a test notification for testing the notification system."
    )
    
    # Create notification
    notification = crud.create_notification(db, notification_data)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create test notification"
        )
    
    # Send WebSocket notification (for demonstration)
    websocket_message = {
        "type": "test_notification",
        "data": {
            "notification_id": notification.notification_id,
            "title": notification.title,
            "message": notification.message,
            "timestamp": notification.created_at.isoformat()
        },
        "timestamp": notification.created_at.isoformat()
    }
    
    # In a real implementation, you would call:
    # await crud.send_to_user(current_user.account_id, websocket_message)
    # For now, we'll just return success
    
    return schemas.MessageResponse(message="Test notification created successfully")