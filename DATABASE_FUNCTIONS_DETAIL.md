# Database Function Signatures - Chi tiết Implementation

## 📋 Tổng hợp các hàm chính theo Interface

### 1. INotificationDatabase Functions

#### CRUD Functions trong `app/crud.py`:
```python
# Lấy notification theo ID
def get_notification(db: Session, notification_id: int) -> models.Notification | None

# Lấy tất cả notifications của user
def get_notifications_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Notification]

# Lấy unread notifications của user
def get_unread_notifications_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Notification]

# Tạo notification mới
def create_notification(db: Session, notification: schemas.NotificationCreate) -> models.Notification

# Tạo notification khi bị outbid
def create_outbid_notification(db: Session, auction_id: int, outbid_user_id: int, new_bidder_id: int, new_bid_price: int) -> models.Notification

# Cập nhật trạng thái đã đọc
def update_notification_status(db: Session, notification_id: int, is_read: bool = True) -> models.Notification | None

# Đánh dấu tất cả notifications là đã đọc
def mark_all_notifications_read(db: Session, user_id: int) -> bool

# Xóa notification
def delete_notification(db: Session, notification_id: int) -> bool

# Đếm số lượng notifications chưa đọc
def get_unread_count(db: Session, user_id: int) -> int
```

#### WebSocket Functions:
```python
# Tạo và gửi notification qua WebSocket
async def create_and_send_notification(db: Session, notification: schemas.NotificationCreate, websocket_message: dict = None)

# Thông báo khi bị outbid
async def notify_bid_outbid(db: Session, auction_id: int, outbid_user_id: int, new_bidder_id: int, new_bid_price: int)
```

#### API Endpoints trong `app/routers/notifications.py`:
```python
# GET /notifications
def get_notifications(skip: int = 0, limit: int = 50, current_user = Depends(get_current_user), db: Session = Depends(get_db))

# GET /notifications/unread
def get_unread_notifications(skip: int = 0, limit: int = 50, current_user = Depends(get_current_user), db: Session = Depends(get_db))

# GET /notifications/unread/count
def get_unread_count(current_user = Depends(get_current_user), db: Session = Depends(get_db))

# PUT /notifications/{notification_id}/read
def mark_as_read(notification_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db))

# PUT /notifications/mark-all-read
def mark_all_read(current_user = Depends(get_current_user), db: Session = Depends(get_db))

# DELETE /notifications/{notification_id}
def delete_notification(notification_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db))

# GET /notifications/auction/{auction_id}
def get_auction_notifications(auction_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db))

# POST /notifications/test
def create_test_notification(current_user = Depends(get_current_user), db: Session = Depends(get_db))
```

---

### 2. IAuthDatabase Functions

#### CRUD Functions trong `app/crud.py`:
```python
# Xác thực tài khoản
def authenticate_account(db: Session, username: str, password: str) -> models.Account | None

# Tạo tài khoản mới
def create_account(db: Session, account: schemas.AccountCreate) -> models.Account

# Lấy account theo username
def get_account_by_username(db: Session, username: str) -> models.Account | None

# Lấy account theo ID
def get_account_by_id(db: Session, account_id: int) -> models.Account | None

# Cập nhật thông tin account
def update_account(db: Session, account_id: int, account_update: schemas.AccountUpdate) -> models.Account | None

# Xóa tài khoản chưa kích hoạt
def delete_unactivated_account(db: Session, username: str) -> bool
```

---

### 3. IProductDatabase Functions

#### CRUD Functions trong `app/crud.py`:
```python
# Lấy product theo ID
def get_product(db: Session, product_id: int) -> models.Product | None

# Lấy tất cả products với phân trang
def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]

# Tạo product mới
def create_product(db: Session, product: schemas.ProductCreate, user_id: int = None) -> models.Product

# Cập nhật product
def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> models.Product | None

# Xóa product
def delete_product(db: Session, product_id: int) -> bool
```

---

### 4. IAuctionDatabase Functions

#### CRUD Functions trong `app/crud.py`:
```python
# Lấy auction theo ID
def get_auction(db: Session, auction_id: int) -> models.Auction | None

# Lấy tất cả auctions với phân trang
def get_auctions(db: Session, skip: int = 0, limit: int = 100) -> List[models.Auction]

# Tạo auction mới
def create_auction(db: Session, auction: schemas.AuctionCreate) -> models.Auction

# Cập nhật auction
def update_auction(db: Session, auction_id: int, auction_update: schemas.AuctionUpdate) -> models.Auction | None

# Xóa auction
def delete_auction(db: Session, auction_id: int) -> bool

# Tìm kiếm auctions
def search_auctions(db: Session, search_params: schemas.AuctionSearch, skip: int = 0, limit: int = 100) -> List[models.Auction]

# Lấy auction với chi tiết
def get_auction_with_details(db: Session, auction_id: int) -> models.Auction | None

# Lấy auctions mà user đã thắng
def get_user_won_auctions(db: Session, user_id: int) -> List[models.Auction]
```

---

### 5. IBidDatabase Functions

#### CRUD Functions trong `app/crud.py`:
```python
# Lấy bid theo ID
def get_bid(db: Session, bid_id: int) -> models.Bid | None

# Lấy bids của auction
def get_bids_by_auction(db: Session, auction_id: int, skip: int = 0, limit: int = 100) -> List[models.Bid]

# Lấy bids của user
def get_bids_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Bid]

# Tạo bid mới
def create_bid(db: Session, bid: schemas.BidCreate, user_id: int) -> models.Bid

# Hủy bid
def cancel_bid(db: Session, bid_id: int, user_id: int) -> bool

# Lấy bid cao nhất hiện tại
def get_current_highest_bid(db: Session, auction_id: int) -> models.Bid | None
```

---

### 6. IPaymentDatabase Functions

#### CRUD Functions trong `app/crud.py`:
```python
# Lấy payment theo ID
def get_payment(db: Session, payment_id: int) -> models.Payment | None

# Lấy payments của user
def get_payments_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Payment]

# Lấy payments của auction
def get_payments_by_auction(db: Session, auction_id: int) -> List[models.Payment]

# Tạo payment mới
def create_payment(db: Session, payment: schemas.PaymentCreate, user_id: int) -> models.Payment

# Cập nhật trạng thái payment
def update_payment_status(db: Session, payment_id: int, status: str) -> models.Payment | None
```

---

## 📝 Parameters Details

### Common Parameters:
- `db: Session` - SQLAlchemy database session
- `user_id: int` - ID của user
- `skip: int = 0` - Số bản ghi bỏ qua (phân trang)
- `limit: int = 100` - Số lượng bản ghi tối đa

### Notification-specific Parameters:
- `notification_id: int` - ID của notification
- `is_read: bool = True` - Trạng thái đã đọc
- `auction_id: int` - ID của auction
- `outbid_user_id: int` - ID của user bị outbid
- `new_bidder_id: int` - ID của user bid mới
- `new_bid_price: int` - Giá bid mới

### WebSocket Parameters:
- `websocket_message: dict = None` - Tin nhắn gửi qua WebSocket

---

## 🔗 Connection Management Functions

```python
# Quản lý kết nối WebSocket
async def add_connection(user_id: int, websocket: WebSocket)
async def remove_connection(user_id: int, websocket: WebSocket)
async def send_to_user(user_id: int, message: dict)
async def broadcast_to_auction_participants(db: Session, auction_id: int, message: dict)
```

---

*Tổng cộng: 15 interface với 40+ CRUD functions và 89+ API endpoints*