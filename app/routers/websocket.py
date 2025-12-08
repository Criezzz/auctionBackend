"""
WebSocket endpoints for real-time notifications
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import json
import asyncio

from .. import crud, schemas
from ..database import SessionLocal
from ..routers.auth import get_current_user
from ..auth import verify_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_websocket_token(token: str) -> dict | None:
    """Verify WebSocket authentication token"""
    try:
        payload = verify_token(token, token_type="access")
        return payload
    except:
        return None


@router.websocket("/notifications/{token}")
async def websocket_notifications(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time notifications
    
    Connect: ws://localhost:8000/ws/notifications/{access_token}
    """
    # Verify token
    payload = await verify_websocket_token(token)
    if not payload:
        await websocket.close(code=4401, reason="Invalid token")
        return
    
    username = payload.get("sub")
    if not username:
        await websocket.close(code=4401, reason="Invalid token payload")
        return
    
    # Get user
    user = crud.get_account_by_username(db, username)
    if not user:
        await websocket.close(code=4401, reason="User not found")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Add connection to active connections
    await crud.add_connection(user.accountID, websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "user_id": user.accountID,
                "username": user.username,
                "message": "Connected to notification service"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send unread notification count
        unread_count = crud.get_unread_count(db, user.accountID)
        await websocket.send_json({
            "type": "unread_count",
            "data": {"count": unread_count},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (ping, subscription changes, etc.)
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "subscribe_auction":
                    auction_id = message_data.get("auction_id")
                    # In a real implementation, you might track subscription preferences
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "data": {"auction_id": auction_id},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "unsubscribe_auction":
                    auction_id = message_data.get("auction_id")
                    await websocket.send_json({
                        "type": "unsubscription_confirmed",
                        "data": {"auction_id": auction_id},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message_type}"},
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON message"},
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            except Exception as e:
                print(f"Error handling WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user.accountID}")
    
    except Exception as e:
        print(f"WebSocket error for user {user.accountID}: {e}")
        try:
            await websocket.close(code=4500, reason="Internal server error")
        except:
            pass
    
    finally:
        # Remove connection from active connections
        await crud.remove_connection(user.accountID, websocket)


@router.websocket("/auction/{auction_id}/{token}")
async def websocket_auction_updates(websocket: WebSocket, auction_id: int, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for auction-specific real-time updates
    
    Connect: ws://localhost:8000/ws/auction/{auction_id}/{access_token}
    """
    # Verify token
    payload = await verify_websocket_token(token)
    if not payload:
        await websocket.close(code=4401, reason="Invalid token")
        return
    
    username = payload.get("sub")
    if not username:
        await websocket.close(code=4401, reason="Invalid token payload")
        return
    
    # Get user
    user = crud.get_account_by_username(db, username)
    if not user:
        await websocket.close(code=4401, reason="User not found")
        return
    
    # Verify auction exists
    auction = crud.get_auction(db, auction_id)
    if not auction:
        await websocket.close(code=4404, reason="Auction not found")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Add connection to active connections
    await crud.add_connection(user.accountID, websocket)
    
    try:
        # Send initial auction data
        current_highest_bid = crud.get_current_highest_bid(db, auction_id)
        highest_bidder = None
        if current_highest_bid:
            highest_bidder = crud.get_account_by_id(db, current_highest_bid.user_id)
        
        await websocket.send_json({
            "type": "auction_initial_data",
            "data": {
                "auction_id": auction_id,
                "auction_name": auction.auctionName,
                "current_highest_bid": current_highest_bid.bidPrice if current_highest_bid else None,
                "highest_bidder_name": f"{highest_bidder.firstName} {highest_bidder.lastName}".strip() if highest_bidder else None,
                "bid_count": len(crud.get_bids_by_auction(db, auction_id)),
                "auction_status": auction.auctionStatus,
                "end_time": auction.endDate.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for ping messages
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            except json.JSONDecodeError:
                break
            except Exception as e:
                print(f"Error handling auction WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        print(f"Auction WebSocket disconnected for user {user.accountID}, auction {auction_id}")
    
    except Exception as e:
        print(f"Auction WebSocket error for user {user.accountID}: {e}")
        try:
            await websocket.close(code=4500, reason="Internal server error")
        except:
            pass
    
    finally:
        # Remove connection
        await crud.remove_connection(user.accountID, websocket)