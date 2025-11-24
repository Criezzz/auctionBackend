"""
Server-Sent Events (SSE) endpoints for real-time notifications
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json
import asyncio

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user

router = APIRouter(prefix="/sse", tags=["Server-Sent Events"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def sse_notifications_stream(user_id: int, db: Session):
    """Generate SSE stream for user notifications"""
    try:
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Send initial unread count
        unread_count = crud.get_unread_count(db, user_id)
        yield f"event: unread_count\ndata: {json.dumps({'count': unread_count})}\n\n"
        
        # Keep connection alive and periodically send heartbeat
        heartbeat_interval = 30  # seconds
        heartbeat_count = 0
        
        while True:
            await asyncio.sleep(1)
            heartbeat_count += 1
            
            # Send heartbeat every 30 seconds
            if heartbeat_count >= heartbeat_interval:
                yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                heartbeat_count = 0
            
            # In a real implementation, you would:
            # 1. Check for new notifications in database
            # 2. Send notification events as they arrive
            # 3. Handle connection cleanup
            
            # For demo purposes, we'll simulate some events
            # You can implement actual notification checking here
                
    except asyncio.CancelledError:
        # Connection closed by client
        yield f"event: disconnected\ndata: {json.dumps({'reason': 'client_disconnected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    except Exception as e:
        # Connection error
        yield f"event: error\ndata: {json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})}\n\n"


async def sse_auction_stream(auction_id: int, db: Session):
    """Generate SSE stream for auction updates"""
    try:
        # Send initial auction data
        auction = crud.get_auction(db, auction_id)
        if auction:
            current_highest_bid = crud.get_current_highest_bid(db, auction_id)
            yield f"event: auction_update\ndata: {json.dumps({
                'auction_id': auction_id,
                'auction_name': auction.auction_name,
                'current_price': current_highest_bid.bid_price if current_highest_bid else None,
                'bid_count': len(crud.get_bids_by_auction(db, auction_id)),
                'status': auction.auction_status,
                'timestamp': datetime.utcnow().isoformat()
            })}\n\n"
        
        # Keep connection alive
        heartbeat_interval = 30
        heartbeat_count = 0
        
        while True:
            await asyncio.sleep(1)
            heartbeat_count += 1
            
            if heartbeat_count >= heartbeat_interval:
                yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat()})}\n\n"
                heartbeat_count = 0
            
            # In real implementation, poll for auction changes
            
    except asyncio.CancelledError:
        yield f"event: disconnected\ndata: {json.dumps({'reason': 'client_disconnected'})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.get("/notifications")
async def sse_notifications(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """SSE endpoint for real-time notifications
    
    Connect: EventSource pointing to /sse/notifications
    Requires: Authorization header with Bearer token
    """
    async def event_generator():
        async for message in sse_notifications_stream(current_user.account_id, db):
            yield message
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/auction/{auction_id}")
async def sse_auction_updates(
    auction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """SSE endpoint for auction-specific updates
    
    Connect: EventSource pointing to /sse/auction/{auction_id}
    Requires: Authorization header with Bearer token
    """
    # Verify auction exists
    auction = crud.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    async def event_generator():
        async for message in sse_auction_stream(auction_id, db):
            yield message
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/test")
async def sse_test(current_user = Depends(get_current_user)):
    """Test SSE endpoint"""
    async def event_generator():
        try:
            # Send test events
            yield f"event: test_start\ndata: {json.dumps({'message': 'SSE test started', 'user': current_user.username})}\n\n"
            
            for i in range(5):
                await asyncio.sleep(1)
                yield f"event: test_message\ndata: {json.dumps({'count': i+1, 'message': f'Test message {i+1}'})}\n\n"
            
            yield f"event: test_end\ndata: {json.dumps({'message': 'SSE test completed'})}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain"
    )


@router.get("/status")
async def sse_status(current_user = Depends(get_current_user)):
    """Get SSE connection status"""
    return {
        "user_id": current_user.account_id,
        "username": current_user.username,
        "available_streams": [
            "/sse/notifications",
            "/sse/test"
        ],
        "documentation": "See API documentation for SSE implementation details"
    }