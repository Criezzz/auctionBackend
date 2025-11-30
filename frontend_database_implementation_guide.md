# Frontend Database Interfaces Implementation Guide

## Tổng Quan
Tài liệu này hướng dẫn cách implement các Database Interfaces theo yêu cầu của thầy. Mỗi interface đại diện cho một "database" trong domain logic và sẽ gọi tới backend API endpoints tương ứng.

## 1. Cấu Trúc Thư Mục Đề Xuất

```
frontend/
├── src/
│   ├── database/
│   │   ├── interfaces/
│   │   │   ├── auth.interface.ts
│   │   │   ├── account.interface.ts
│   │   │   ├── product.interface.ts
│   │   │   ├── auction.interface.ts
│   │   │   ├── bid.interface.ts
│   │   │   ├── participation.interface.ts
│   │   │   ├── payment.interface.ts
│   │   │   ├── search.interface.ts
│   │   │   ├── notification.interface.ts
│   │   │   ├── bank.interface.ts
│   │   │   ├── status.interface.ts
│   │   │   ├── realtime.interface.ts
│   │   │   └── database-factory.interface.ts
│   │   ├── implementations/
│   │   │   ├── api/
│   │   │   │   ├── auth.api.ts
│   │   │   │   ├── account.api.ts
│   │   │   │   └── ...
│   │   │   └── mock/
│   │   │       ├── auth.mock.ts
│   │   │       └── ...
│   │   ├── factories/
│   │   │   └── database.factory.ts
│   │   ├── api-client/
│   │   │   └── api-client.ts
│   │   └── types/
│   │       └── models.ts
```

## 2. TypeScript Data Models

### frontend/src/database/types/models.ts

```typescript
// ===== USER TYPES =====
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  first_name?: string;
  last_name?: string;
  phone_num?: string;
  date_of_birth?: string;
  activated: boolean;
  is_authenticated: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserRegistration {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_num: string;
  date_of_birth?: string;
}

export interface ProfileUpdate {
  first_name?: string;
  last_name?: string;
  phone_num?: string;
  email?: string;
  date_of_birth?: string;
}

// ===== AUTH TYPES =====
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  otp_token: string;
  expires_in: number;
  user: User;
}

export interface OTPVerification {
  otp_code: string;
  otp_token: string;
  username: string;
}

export interface OTPResponse {
  success: boolean;
  message: string;
  remaining_trials: number;
}

// ===== PRODUCT TYPES =====
export interface Product {
  product_id: number;
  product_name: string;
  product_description?: string;
  product_type?: string;
  shipping_status?: string;
  approval_status: 'pending' | 'approved' | 'rejected';
  rejection_reason?: string;
  suggested_by_user_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface ProductCreate {
  product_name: string;
  product_description: string;
  product_type: string;
}

export interface ProductUpdate {
  product_name?: string;
  shipping_status?: 'pending' | 'approved' | 'rejected' | 'sold' | 'shipped' | 'delivered';
}

// ===== AUCTION TYPES =====
export interface Auction {
  auction_id: number;
  auction_name: string;
  product_id: number;
  start_date: string;
  end_date: string;
  price_step: number;
  auction_status: 'pending' | 'active' | 'ended' | 'cancelled';
  bid_winner_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface DetailedAuction extends Auction {
  product: Product;
  bids: Bid[];
  current_price: number;
}

export interface AuctionCreate {
  auction_name: string;
  product_id: number;
  start_date: string;
  end_date: string;
  price_step: number;
}

export interface AuctionUpdate {
  auction_name?: string;
  start_date?: string;
  end_date?: string;
  auction_status?: string;
}

export interface AuctionSearch {
  auction_name?: string;
  auction_status?: string;
  product_type?: string;
  min_price_step?: number;
  max_price_step?: number;
}

// ===== BID TYPES =====
export interface Bid {
  bid_id: number;
  auction_id: number;
  user_id: number;
  bid_price: number;
  bid_status: 'active' | 'cancelled';
  created_at: string;
}

export interface BidCreate {
  auction_id: number;
  bid_price: number;
}

export interface BidStatusResponse {
  has_bids: boolean;
  is_leading: boolean;
  total_bids: number;
  highest_bid: number;
  latest_bid: string;
  auction_status: string;
  time_remaining: number;
}

// ===== PAYMENT TYPES =====
export interface Payment {
  payment_id: number;
  auction_id: number;
  user_id: number;
  payment_status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  payment_type: 'deposit' | 'final_payment';
  amount: number;
  first_name: string;
  last_name: string;
  user_address: string;
  user_receiving_option: 'shipping' | 'pickup';
  user_payment_method: 'bank_transfer' | 'credit_card' | 'cash';
  created_at: string;
}

export interface PaymentCreate {
  auction_id: number;
  first_name: string;
  last_name: string;
  user_address: string;
  user_receiving_option: 'shipping' | 'pickup';
  user_payment_method: 'bank_transfer' | 'credit_card' | 'cash';
}

export interface PaymentTokenStatus {
  valid: boolean;
  payment_id?: number;
  user_id?: number;
  amount?: number;
  expires_at?: string;
  remaining_minutes: number;
  remaining_seconds: number;
  error?: string;
}

// ===== OTHER TYPES =====
export interface MessageResponse {
  message: string;
  success: boolean;
}

export interface SearchQuery {
  auction_name?: string;
  auction_status?: string;
  product_type?: string;
  min_price_step?: number;
  max_price_step?: number;
}
```

## 3. API Client Base Implementation

### frontend/src/database/api-client/api-client.ts

```typescript
export class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.loadTokensFromStorage();
  }

  private loadTokensFromStorage(): void {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private saveTokensToStorage(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const config: RequestInit = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401 && this.refreshToken) {
        // Try to refresh token
        const newTokens = await this.refreshToken();
        if (newTokens) {
          this.saveTokensToStorage(newTokens.access_token, newTokens.refresh_token);
          
          // Retry original request with new token
          headers['Authorization'] = `Bearer ${newTokens.access_token}`;
          const retryResponse = await fetch(url, config);
          
          if (!retryResponse.ok) {
            throw new Error(`HTTP error! status: ${retryResponse.status}`);
          }
          
          return retryResponse.json() as Promise<T>;
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response.json() as Promise<T>;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async refreshToken(): Promise<TokenResponse | null> {
    if (!this.refreshToken) {
      return null;
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken
        })
      });

      if (response.ok) {
        const tokens: TokenResponse = await response.json();
        this.saveTokensToStorage(tokens.access_token, tokens.refresh_token);
        return tokens;
      } else {
        this.clearTokens();
        return null;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.clearTokens();
      return null;
    }
  }

  logout(): void {
    this.clearTokens();
  }
}
```

## 4. Interface Definitions

### frontend/src/database/interfaces/auth.interface.ts

```typescript
import { TokenResponse, RegisterResponse, OTPVerification, OTPResponse, User, UserRegistration, ProfileUpdate } from '../types/models';

export interface IAuthDatabase {
  // Authentication methods
  login(username: string, password: string): Promise<TokenResponse>;
  logout(): Promise<void>;
  refreshToken(refreshToken: string): Promise<TokenResponse>;
  
  // Registration with OTP
  register(userData: UserRegistration): Promise<RegisterResponse>;
  verifyOTP(otpData: OTPVerification): Promise<OTPResponse>;
  resendOTP(username: string): Promise<RegisterResponse>;
  cancelRegistration(username: string): Promise<RegisterResponse>;
  
  // Password recovery
  recoverPassword(username: string): Promise<RegisterResponse>;
  verifyRecoveryOTP(otpData: OTPVerification): Promise<OTPResponse>;
  resetPassword(resetToken: string, newPassword: string): Promise<RegisterResponse>;
  
  // OTP management
  getOTPStatus(otpToken: string): Promise<OTPResponse>;
  
  // User info
  getCurrentUser(): Promise<User>;
}
```

### frontend/src/database/interfaces/account.interface.ts

```typescript
import { User, ProfileUpdate } from '../types/models';

export interface IAccountDatabase {
  getProfile(): Promise<User>;
  updateProfile(profileData: ProfileUpdate): Promise<User>;
  getAccountById(accountId: number): Promise<User>;
}
```

### frontend/src/database/interfaces/auction.interface.ts

```typescript
import { Auction, DetailedAuction, AuctionCreate, AuctionUpdate } from '../types/models';
import { MessageResponse } from '../types/models';

export interface IAuctionDatabase {
  registerAuction(auctionData: AuctionCreate): Promise<Auction>;
  getAllAuctions(skip?: number, limit?: number): Promise<Auction[]>;
  getAuctionById(auctionId: number): Promise<DetailedAuction>;
  updateAuction(auctionId: number, updateData: AuctionUpdate): Promise<Auction>;
  deleteAuction(auctionId: number): Promise<MessageResponse>;
  getRegisteredAuctions(): Promise<Auction[]>;
}
```

### frontend/src/database/interfaces/bid.interface.ts

```typescript
import { Bid, BidCreate, BidStatusResponse } from '../types/models';
import { MessageResponse } from '../types/models';

export interface IBidDatabase {
  placeBid(bidData: BidCreate): Promise<Bid>;
  cancelBid(bidId: number): Promise<MessageResponse>;
  getMyBids(skip?: number, limit?: number): Promise<Bid[]>;
  getAuctionBids(auctionId: number, skip?: number, limit?: number): Promise<Bid[]>;
  getHighestBid(auctionId: number): Promise<Bid>;
  getMyBidStatus(auctionId: number): Promise<BidStatusResponse>;
}
```

### frontend/src/database/interfaces/payment.interface.ts

```typescript
import { Payment, PaymentCreate, PaymentTokenStatus } from '../types/models';
import { MessageResponse } from '../types/models';

export interface IPaymentDatabase {
  createPayment(paymentData: PaymentCreate): Promise<Payment>;
  getMyPayments(): Promise<Payment[]>;
  getAuctionPayment(auctionId: number): Promise<Payment>;
  getPaymentById(paymentId: number): Promise<Payment>;
  updatePaymentStatus(paymentId: number, status: string): Promise<Payment>;
  getPendingPayments(): Promise<Payment[]>;
  processPayment(paymentId: number): Promise<MessageResponse>;
  getPaymentTokenStatus(token: string): Promise<PaymentTokenStatus>;
  qrCallback(token: string): Promise<any>;
  getPaymentsByStatus(status: string): Promise<Payment[]>;
}
```

## 5. Concrete Implementation Example

### frontend/src/database/implementations/api/auth.api.ts

```typescript
import { IAuthDatabase } from '../../interfaces/auth.interface';
import { ApiClient } from '../../api-client/api-client';
import { 
  TokenResponse, 
  RegisterResponse, 
  OTPVerification, 
  OTPResponse, 
  User, 
  UserRegistration 
} from '../../types/models';

export class AuthApiDatabase implements IAuthDatabase {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async login(username: string, password: string): Promise<TokenResponse> {
    return this.apiClient.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  }

  async logout(): Promise<void> {
    try {
      await this.apiClient.request('/auth/logout', {
        method: 'POST'
      });
    } finally {
      this.apiClient.logout();
    }
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return this.apiClient.request<TokenResponse>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });
  }

  async register(userData: UserRegistration): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async verifyOTP(otpData: OTPVerification): Promise<OTPResponse> {
    return this.apiClient.request<OTPResponse>('/auth/register/verify', {
      method: 'POST',
      body: JSON.stringify(otpData)
    });
  }

  async resendOTP(username: string): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/register/resend', {
      method: 'POST',
      body: JSON.stringify({ username })
    });
  }

  async cancelRegistration(username: string): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/register/cancel', {
      method: 'POST',
      body: JSON.stringify({ username })
    });
  }

  async recoverPassword(username: string): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/recover', {
      method: 'POST',
      body: JSON.stringify({ username })
    });
  }

  async verifyRecoveryOTP(otpData: OTPVerification): Promise<OTPResponse> {
    return this.apiClient.request<OTPResponse>('/auth/recover/verify', {
      method: 'POST',
      body: JSON.stringify(otpData)
    });
  }

  async resetPassword(resetToken: string, newPassword: string): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/reset', {
      method: 'POST',
      body: JSON.stringify({ reset_token: resetToken, new_password: newPassword })
    });
  }

  async getOTPStatus(otpToken: string): Promise<OTPResponse> {
    return this.apiClient.request<OTPResponse>(`/auth/otp/status?otp_token=${otpToken}`);
  }

  async getCurrentUser(): Promise<User> {
    return this.apiClient.request<User>('/auth/me');
  }
}
```

### frontend/src/database/implementations/api/account.api.ts

```typescript
import { IAccountDatabase } from '../../interfaces/account.interface';
import { ApiClient } from '../../api-client/api-client';
import { User, ProfileUpdate } from '../../types/models';

export class AccountApiDatabase implements IAccountDatabase {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async getProfile(): Promise<User> {
    return this.apiClient.request<User>('/accounts/profile');
  }

  async updateProfile(profileData: ProfileUpdate): Promise<User> {
    return this.apiClient.request<User>('/accounts/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  async getAccountById(accountId: number): Promise<User> {
    return this.apiClient.request<User>(`/accounts/${accountId}`);
  }
}
```

## 6. Factory Pattern Implementation

### frontend/src/database/interfaces/database-factory.interface.ts

```typescript
import { 
  IAuthDatabase, 
  IAccountDatabase, 
  IAuctionDatabase, 
  IBidDatabase,
  IPaymentDatabase
  // ... import all interfaces
} from './index';

export interface IDatabaseFactory {
  createAuthDatabase(): IAuthDatabase;
  createAccountDatabase(): IAccountDatabase;
  createAuctionDatabase(): IAuctionDatabase;
  createBidDatabase(): IBidDatabase;
  createParticipationDatabase(): IParticipationDatabase;
  createPaymentDatabase(): IPaymentDatabase;
  createSearchDatabase(): ISearchDatabase;
  createNotificationDatabase(): INotificationDatabase;
  createBankDatabase(): IBankDatabase;
  createStatusDatabase(): IStatusDatabase;
  createRealTimeDatabase(): IRealTimeDatabase;
}
```

### frontend/src/database/factories/database.factory.ts

```typescript
import { IDatabaseFactory } from '../interfaces/database-factory.interface';
import { ApiClient } from '../api-client/api-client';

// Import all API implementations
import { AuthApiDatabase } from '../implementations/api/auth.api';
import { AccountApiDatabase } from '../implementations/api/account.api';
import { AuctionApiDatabase } from '../implementations/api/auction.api';
// ... import other implementations

export class ApiDatabaseFactory implements IDatabaseFactory {
  private apiClient: ApiClient;

  constructor(apiClient?: ApiClient) {
    this.apiClient = apiClient || new ApiClient();
  }

  createAuthDatabase(): IAuthDatabase {
    return new AuthApiDatabase(this.apiClient);
  }

  createAccountDatabase(): IAccountDatabase {
    return new AccountApiDatabase(this.apiClient);
  }

  createAuctionDatabase(): IAuctionDatabase {
    return new AuctionApiDatabase(this.apiClient);
  }

  createBidDatabase(): IBidDatabase {
    return new BidApiDatabase(this.apiClient);
  }

  // ... implement other database creators
}
```

## 7. Service Layer Usage Example

### frontend/src/services/auction.service.ts

```typescript
import { 
  IAuctionDatabase, 
  IBidDatabase, 
  IParticipationDatabase 
} from '../database/interfaces';
import { 
  Auction, 
  DetailedAuction, 
  Bid, 
  BidCreate 
} from '../database/types/models';

export class AuctionService {
  private auctionDb: IAuctionDatabase;
  private bidDb: IBidDatabase;
  private participationDb: IParticipationDatabase;

  constructor(databaseFactory: IDatabaseFactory) {
    this.auctionDb = databaseFactory.createAuctionDatabase();
    this.bidDb = databaseFactory.createBidDatabase();
    this.participationDb = databaseFactory.createParticipationDatabase();
  }

  async getActiveAuctions(): Promise<Auction[]> {
    return this.auctionDb.getAllAuctions(0, 100);
  }

  async getAuctionDetails(auctionId: number): Promise<DetailedAuction> {
    return this.auctionDb.getAuctionById(auctionId);
  }

  async placeBid(auctionId: number, bidPrice: number): Promise<Bid> {
    // Check if user is registered for this auction first
    const participationStatus = await this.participationDb.getParticipationStatus(auctionId);
    if (!participationStatus.is_registered) {
      throw new Error('Bạn phải đăng ký tham gia đấu giá trước khi đặt giá');
    }

    // Place the bid
    return this.bidDb.placeBid({ auction_id: auctionId, bid_price: bidPrice });
  }

  async getMyBidStatus(auctionId: number): Promise<any> {
    return this.bidDb.getMyBidStatus(auctionId);
  }

  async cancelBid(bidId: number): Promise<void> {
    await this.bidDb.cancelBid(bidId);
  }
}
```

## 8. Mock Implementation Example (for Testing)

### frontend/src/database/implementations/mock/auth.mock.ts

```typescript
import { IAuthDatabase } from '../../interfaces/auth.interface';
import { 
  TokenResponse, 
  RegisterResponse, 
  OTPVerification, 
  OTPResponse, 
  User 
} from '../../types/models';

// Mock data
const mockUser: User = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'user',
  first_name: 'Test',
  last_name: 'User',
  activated: true,
  is_authenticated: true,
  created_at: new Date().toISOString()
};

export class AuthMockDatabase implements IAuthDatabase {
  private isLoggedIn = false;

  async login(username: string, password: string): Promise<TokenResponse> {
    if (username === 'test' && password === 'test') {
      this.isLoggedIn = true;
      return {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 1800
      };
    }
    throw new Error('Invalid credentials');
  }

  async logout(): Promise<void> {
    this.isLoggedIn = false;
  }

  async getCurrentUser(): Promise<User> {
    if (!this.isLoggedIn) {
      throw new Error('Not authenticated');
    }
    return mockUser;
  }

  // ... implement other methods with mock data
}
```

## 9. Configuration và Dependency Injection

### frontend/src/config/database.config.ts

```typescript
import { IDatabaseFactory } from '../database/interfaces/database-factory.interface';
import { ApiDatabaseFactory } from '../database/factories/database.factory';
import { MockDatabaseFactory } from '../database/factories/mock-database.factory';

export enum DatabaseEnvironment {
  DEVELOPMENT = 'development',
  TESTING = 'testing',
  PRODUCTION = 'production'
}

export class DatabaseConfig {
  private static instance: DatabaseConfig;
  private databaseFactory: IDatabaseFactory;

  private constructor() {
    const environment = process.env.NODE_ENV || DatabaseEnvironment.DEVELOPMENT;
    
    if (environment === DatabaseEnvironment.TESTING) {
      this.databaseFactory = new MockDatabaseFactory();
    } else {
      this.databaseFactory = new ApiDatabaseFactory();
    }
  }

  static getInstance(): DatabaseConfig {
    if (!DatabaseConfig.instance) {
      DatabaseConfig.instance = new DatabaseConfig();
    }
    return DatabaseConfig.instance;
  }

  getDatabaseFactory(): IDatabaseFactory {
    return this.databaseFactory;
  }
}
```

## 10. Benefits của Architecture này

1. **Interface Segregation**: Mỗi interface xử lý một domain cụ thể
2. **Dependency Inversion**: Frontend phụ thuộc vào abstractions, không phải concrete implementations
3. **Testability**: Dễ dàng mock interfaces cho unit testing
4. **Maintainability**: Clear separation of concerns theo domain
5. **Flexibility**: Có thể dễ dàng chuyển đổi giữa mock và real API
6. **Scalability**: Dễ dàng thêm interfaces mới cho features mới
7. **Type Safety**: Full TypeScript support với comprehensive interfaces

## 11. Next Steps

1. Implement tất cả concrete database classes
2. Create comprehensive error handling
3. Add caching layer cho frequently accessed data
4. Implement retry mechanisms cho failed requests
5. Add loading states và progress indicators
6. Create comprehensive unit tests
7. Add integration tests với real backend

---

**Lưu ý**: Đây là thiết kế theo yêu cầu Interface-based architecture của thầy. Mỗi interface đại diện cho một "database" trong domain logic và sẽ gọi tới backend API endpoints tương ứng theo mapping trong `API_ENDPOINTS_GUIDE.md`.