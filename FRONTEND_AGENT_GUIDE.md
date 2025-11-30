# Frontend Agent Guide - React Implementation với Interface-based Architecture

## 🎯 Tổng Quan
Sử dụng **React + TypeScript** để implement frontend với Interface-based architecture theo yêu cầu của thầy. Tập trung vào 12 Database Interfaces và mapping với backend API endpoints.

## 📋 Backend Context (89+ Endpoints)

**Backend có 14 domain chính:**
- Authentication (`/auth`) - JWT, OTP verification, password recovery
- User Account (`/accounts`) - Profile management  
- Products (`/products`) - Product CRUD
- Images (`/images`) - Local image storage system
- Auctions (`/auctions`) - Auction management
- Bids (`/bids`) - Bidding system
- Participation (`/participation`) - Auction registration
- Payments (`/payments`) - Payment với QR system
- Bank (`/bank`) - Mock bank integration
- Search (`/search`) - Search & filteringlu
- Notifications (`/notifications`) - Notification management
- Status (`/status`) - Status management
- Real-time SSE (`/sse`) - Server-Sent Events
- Real-time WebSocket (`/websocket`) - Live updates

## 🏗️ Interface-based Architecture (theo yêu cầu thầy)

### 1. Database Interfaces (14 interfaces chính)

```typescript
// src/database/interfaces/index.ts
export interface IAuthDatabase {
  login(username: string, password: string): Promise<TokenResponse>;
  register(userData: UserRegistration): Promise<RegisterResponse>;
  verifyOTP(data: OTPVerification): Promise<OTPResponse>;
  getCurrentUser(): Promise<User>;
  logout(): Promise<void>;
}

export interface IAccountDatabase {
  getProfile(): Promise<User>;
  updateProfile(data: ProfileUpdate): Promise<User>;
}

export interface IAuctionDatabase {
  getAllAuctions(skip?: number, limit?: number): Promise<Auction[]>;
  getAuctionById(id: number): Promise<DetailedAuction>;
  createAuction(data: AuctionCreate): Promise<Auction>;
}

export interface IBidDatabase {
  placeBid(data: BidCreate): Promise<Bid>;
  cancelBid(id: number): Promise<void>;
  getMyBids(): Promise<Bid[]>;
  getHighestBid(auctionId: number): Promise<Bid>;
}

export interface IPaymentDatabase {
  createPayment(data: PaymentCreate): Promise<Payment>;
  getMyPayments(): Promise<Payment[]>;
  getPaymentTokenStatus(token: string): Promise<PaymentTokenStatus>;
  qrCallback(token: string): Promise<any>;
}

export interface INotificationDatabase {
  getNotifications(): Promise<Notification[]>;
  getUnreadCount(): Promise<number>;
  markAsRead(id: number): Promise<void>;
}

export interface IRealTimeDatabase {
  connectNotifications(token: string): Promise<EventSource>;
  connectAuction(auctionId: number, token: string): Promise<WebSocket>;
  disconnect(): void;
}

// Factory interface
export interface IDatabaseFactory {
  createAuthDatabase(): IAuthDatabase;
  createAccountDatabase(): IAccountDatabase;
  createProductDatabase(): IProductDatabase;
  createImageDatabase(): IImageDatabase;
  createAuctionDatabase(): IAuctionDatabase;
  createBidDatabase(): IBidDatabase;
  createParticipationDatabase(): IParticipationDatabase;
  createPaymentDatabase(): IPaymentDatabase;
  createBankDatabase(): IBankDatabase;
  createSearchDatabase(): ISearchDatabase;
  createNotificationDatabase(): INotificationDatabase;
  createStatusDatabase(): IStatusDatabase;
  createSSEDatabase(): ISSEDatabase;
  createWebSocketDatabase(): IWebSocketDatabase;
}
```

### 2. API Client Implementation

```typescript
// src/database/api-client/ApiClient.ts
export class ApiClient {
  private baseUrl = 'http://localhost:8000';
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.loadTokensFromStorage();
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });
      
      if (response.status === 401 && this.refreshToken) {
        // Try to refresh token
        const newTokens = await this.refreshToken();
        if (newTokens) {
          headers['Authorization'] = `Bearer ${newTokens.access_token}`;
          const retryResponse = await fetch(url, { ...options, headers });
          if (!retryResponse.ok) throw new Error(`HTTP ${retryResponse.status}`);
          return retryResponse.json();
        }
      }

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  private async refreshToken(): Promise<TokenResponse | null> {
    if (!this.refreshToken) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });

      if (response.ok) {
        const tokens = await response.json();
        this.saveTokens(tokens.access_token, tokens.refresh_token);
        return tokens;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }
    return null;
  }

  private loadTokensFromStorage(): void {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private saveTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  logout(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}
```

### 3. Concrete Implementations

```typescript
// src/database/implementations/AuthApiDatabase.ts
import { IAuthDatabase } from '../interfaces';
import { TokenResponse, RegisterResponse, OTPVerification, User, UserRegistration } from '../types';

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

  async register(userData: UserRegistration): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async verifyOTP(data: OTPVerification): Promise<RegisterResponse> {
    return this.apiClient.request<RegisterResponse>('/auth/register/verify', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.apiClient.request<User>('/auth/me');
  }

  async logout(): Promise<void> {
    await this.apiClient.request('/auth/logout', { method: 'POST' });
    this.apiClient.logout();
  }
}

// src/database/implementations/AuctionApiDatabase.ts
import { IAuctionDatabase } from '../interfaces';
import { Auction, DetailedAuction, AuctionCreate } from '../types';

export class AuctionApiDatabase implements IAuctionDatabase {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async getAllAuctions(skip = 0, limit = 100): Promise<Auction[]> {
    return this.apiClient.request<Auction[]>(`/auctions?skip=${skip}&limit=${limit}`);
  }

  async getAuctionById(id: number): Promise<DetailedAuction> {
    return this.apiClient.request<DetailedAuction>(`/auctions/${id}`);
  }

  async createAuction(data: AuctionCreate): Promise<Auction> {
    return this.apiClient.request<Auction>('/auctions/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
}
```

### 4. Factory Pattern

```typescript
// src/database/factories/DatabaseFactory.ts
import { IDatabaseFactory } from '../interfaces';
import { ApiClient } from '../api-client/ApiClient';
import { AuthApiDatabase } from '../implementations/AuthApiDatabase';
import { AuctionApiDatabase } from '../implementations/AuctionApiDatabase';

export class DatabaseFactory implements IDatabaseFactory {
  private apiClient: ApiClient;

  constructor() {
    this.apiClient = new ApiClient();
  }

  createAuthDatabase(): IAuthDatabase {
    return new AuthApiDatabase(this.apiClient);
  }

  createAuctionDatabase(): IAuctionDatabase {
    return new AuctionApiDatabase(this.apiClient);
  }

  // Implement các factory methods khác...
}
```

## 🎨 React Integration

### 1. React Context cho Database

```typescript
// src/contexts/DatabaseContext.tsx
import React, { createContext, useContext, ReactNode } from 'react';
import { IDatabaseFactory } from '../database/interfaces';
import { DatabaseFactory } from '../database/factories/DatabaseFactory';

interface DatabaseContextType {
  dbFactory: IDatabaseFactory;
}

const DatabaseContext = createContext<DatabaseContextType | undefined>(undefined);

export const DatabaseProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const dbFactory = new DatabaseFactory();

  return (
    <DatabaseContext.Provider value={{ dbFactory }}>
      {children}
    </DatabaseContext.Provider>
  );
};

export const useDatabase = () => {
  const context = useContext(DatabaseContext);
  if (!context) {
    throw new Error('useDatabase must be used within DatabaseProvider');
  }
  return context.dbFactory;
};
```

### 2. React Hooks cho Database Operations

```typescript
// src/hooks/useAuth.ts
import { useState, useEffect, useCallback } from 'react';
import { useDatabase } from '../contexts/DatabaseContext';
import { User, UserRegistration, TokenResponse } from '../database/types';

export const useAuth = () => {
  const dbFactory = useDatabase();
  const authDb = dbFactory.createAuthDatabase();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    try {
      const tokens: TokenResponse = await authDb.login(username, password);
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      
      const currentUser = await authDb.getCurrentUser();
      setUser(currentUser);
    } finally {
      setLoading(false);
    }
  }, [authDb]);

  const register = useCallback(async (userData: UserRegistration) => {
    setLoading(true);
    try {
      return await authDb.register(userData);
    } finally {
      setLoading(false);
    }
  }, [authDb]);

  const logout = useCallback(async () => {
    await authDb.logout();
    setUser(null);
  }, [authDb]);

  const checkAuth = useCallback(async () => {
    try {
      const currentUser = await authDb.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.log('Not authenticated');
    }
  }, [authDb]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };
};
```

### 3. React Components Example

```typescript
// src/components/AuctionList.tsx
import React, { useState, useEffect } from 'react';
import { useDatabase } from '../contexts/DatabaseContext';
import { Auction } from '../database/types';

export const AuctionList: React.FC = () => {
  const dbFactory = useDatabase();
  const auctionDb = dbFactory.createAuctionDatabase();
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAuctions = async () => {
      try {
        const data = await auctionDb.getAllAuctions(0, 50);
        setAuctions(data);
      } catch (error) {
        console.error('Failed to fetch auctions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAuctions();
  }, [auctionDb]);

  if (loading) return <div>Loading auctions...</div>;

  return (
    <div>
      <h2>Active Auctions</h2>
      <div className="auction-grid">
        {auctions.map(auction => (
          <div key={auction.auction_id} className="auction-card">
            <h3>{auction.auction_name}</h3>
            <p>Ends: {new Date(auction.end_date).toLocaleString()}</p>
            <p>Price Step: {auction.price_step} VND</p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 4. Real-time Integration

```typescript
// src/hooks/useRealTime.ts
import { useEffect, useRef, useCallback } from 'react';
import { useDatabase } from '../contexts/DatabaseContext';

export const useRealTime = (auctionId: number | null) => {
  const dbFactory = useDatabase();
  const realTimeDb = dbFactory.createRealTimeDatabase();
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback((token: string) => {
    if (!auctionId) return;

    // Connect to auction updates
    const ws = realTimeDb.connectAuction(auctionId, token);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Real-time update:', data);
      // Handle different message types
    };

    return ws;
  }, [auctionId, realTimeDb]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    realTimeDb.disconnect();
  }, [realTimeDb]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      const connection = connect(token);
      return disconnect;
    }
  }, [connect, disconnect]);

  return { connect, disconnect };
};
```

## 📝 TypeScript Types

```typescript
// src/database/types/index.ts
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  first_name?: string;
  last_name?: string;
  activated: boolean;
  is_authenticated: boolean;
  created_at: string;
}

export interface Auction {
  auction_id: number;
  auction_name: string;
  product_id: number;
  start_date: string;
  end_date: string;
  price_step: number;
  auction_status: 'pending' | 'active' | 'ended' | 'cancelled';
  created_at: string;
}

export interface Bid {
  bid_id: number;
  auction_id: number;
  user_id: number;
  bid_price: number;
  bid_status: 'active' | 'cancelled';
  created_at: string;
}

export interface Payment {
  payment_id: number;
  auction_id: number;
  user_id: number;
  payment_status: 'pending' | 'processing' | 'completed' | 'failed';
  payment_type: 'deposit' | 'final_payment';
  amount: number;
  created_at: string;
}

// Add more types as needed...
```

## 🎯 Key Points

1. **Interface-based architecture** theo yêu cầu thầy
2. **14 Database interfaces** map với 14 backend domains  
3. **Factory pattern** để khởi tạo database instances
4. **React Context** cung cấp database factory cho toàn app
5. **Custom hooks** cho auth, auctions, real-time features
6. **TypeScript** đảm bảo type safety
7. **JWT authentication** được handle tự động trong ApiClient
8. **Real-time** via WebSocket và SSE cho auction updates
9. **Image management** với local storage system
10. **QR Payment system** với time-sensitive tokens

## 🚀 Setup Steps

1. Tạo folder structure theo guide này
2. Install dependencies: `npm install react typescript`
3. Implement ApiClient với authentication
4. Tạo các Database interfaces  
5. Implement concrete classes (AuthApiDatabase, AuctionApiDatabase, etc.)
6. Tạo Factory pattern
7. Setup React Context và hooks
8. Build React components sử dụng hooks

**Lưu ý**: Đây là foundation để build React frontend với Interface-based architecture. Extend thêm các interfaces và implementations khi cần thiết.