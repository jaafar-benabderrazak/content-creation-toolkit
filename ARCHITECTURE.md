# LibreWork - Space Reservation Platform Architecture

## Overview

LibreWork is a platform allowing users to find and reserve spaces in cafes, libraries, and other establishments for specific timeslots. The system uses a credit-based economy (symbolic coffee) and QR codes for reservation validation.

## Tech Stack

- **Frontend**: Next.js 14+ (App Router), TypeScript, TailwindCSS
- **Backend**: Python FastAPI
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Real-time**: Supabase Realtime subscriptions
- **Storage**: Supabase Storage (for venue images, QR codes)
- **Deployment**: 
  - Frontend: Vercel
  - Backend: Railway/Fly.io
  - Database: Supabase Cloud

## System Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Next.js       │─────▶│   FastAPI        │─────▶│   Supabase      │
│   Frontend      │◀─────│   Backend        │◀─────│   PostgreSQL    │
│   (Vercel)      │      │   (Railway)      │      │   (Cloud)       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
        │                         │                          │
        │                         │                          │
        ▼                         ▼                          ▼
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  User Devices   │      │  QR Code Gen     │      │  Realtime       │
│  (Mobile/Web)   │      │  Validation      │      │  Subscriptions  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

## Database Schema

### Core Entities

#### users
- id (uuid, PK)
- email (text, unique)
- full_name (text)
- role (enum: 'customer', 'owner', 'admin')
- coffee_credits (integer, default: 10)
- created_at (timestamp)
- updated_at (timestamp)

#### establishments
- id (uuid, PK)
- owner_id (uuid, FK -> users)
- name (text)
- description (text)
- address (text)
- city (text)
- latitude (decimal)
- longitude (decimal)
- category (enum: 'cafe', 'library', 'coworking', 'restaurant')
- opening_hours (jsonb) - {day: {open: "09:00", close: "18:00"}}
- images (text[])
- amenities (text[]) - ['wifi', 'power_outlets', 'quiet', 'food', 'drinks']
- is_active (boolean, default: true)
- created_at (timestamp)
- updated_at (timestamp)

#### spaces
- id (uuid, PK)
- establishment_id (uuid, FK -> establishments)
- name (text) - "Table 1", "Room A"
- space_type (enum: 'table', 'room', 'desk', 'booth')
- capacity (integer)
- qr_code (text) - unique QR code identifier
- qr_code_image_url (text)
- is_available (boolean, default: true)
- created_at (timestamp)
- updated_at (timestamp)

#### reservations
- id (uuid, PK)
- user_id (uuid, FK -> users)
- space_id (uuid, FK -> spaces)
- establishment_id (uuid, FK -> establishments)
- start_time (timestamp)
- end_time (timestamp)
- status (enum: 'pending', 'confirmed', 'checked_in', 'completed', 'cancelled')
- cost_credits (integer)
- validation_code (text) - 6-digit code for validation
- checked_in_at (timestamp, nullable)
- created_at (timestamp)
- updated_at (timestamp)

#### credit_transactions
- id (uuid, PK)
- user_id (uuid, FK -> users)
- amount (integer) - positive for credit, negative for debit
- transaction_type (enum: 'purchase', 'reservation', 'cancellation_refund', 'bonus')
- reservation_id (uuid, FK -> reservations, nullable)
- description (text)
- created_at (timestamp)

#### reviews
- id (uuid, PK)
- user_id (uuid, FK -> users)
- establishment_id (uuid, FK -> establishments)
- reservation_id (uuid, FK -> reservations)
- rating (integer) - 1-5
- comment (text, nullable)
- created_at (timestamp)
- updated_at (timestamp)

### Indexes
- establishments: (latitude, longitude) - for geospatial queries
- reservations: (start_time, end_time, space_id) - for availability checks
- reservations: (user_id, status) - for user reservation history
- spaces: (establishment_id, is_available)

### Row Level Security (RLS)
- Users can only view their own profile and credits
- Establishment owners can only manage their own establishments
- All users can view active establishments and available spaces
- Users can only view their own reservations
- Owners can view reservations for their establishments

## API Architecture

### Backend (FastAPI) Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

#### Establishments
- `GET /api/v1/establishments` - List establishments (with filters: category, city, nearest)
- `GET /api/v1/establishments/{id}` - Get establishment details
- `POST /api/v1/establishments` - Create establishment (owner only)
- `PUT /api/v1/establishments/{id}` - Update establishment (owner only)
- `DELETE /api/v1/establishments/{id}` - Delete establishment (owner only)
- `GET /api/v1/establishments/nearest` - Get nearest establishments (lat, lng, radius)
- `GET /api/v1/establishments/{id}/availability` - Check space availability

#### Spaces
- `GET /api/v1/spaces` - List spaces by establishment
- `POST /api/v1/spaces` - Create space (owner only)
- `PUT /api/v1/spaces/{id}` - Update space (owner only)
- `DELETE /api/v1/spaces/{id}` - Delete space (owner only)
- `GET /api/v1/spaces/{id}/qr-code` - Generate/retrieve QR code

#### Reservations
- `GET /api/v1/reservations` - List user reservations
- `POST /api/v1/reservations` - Create reservation
- `GET /api/v1/reservations/{id}` - Get reservation details
- `PUT /api/v1/reservations/{id}/cancel` - Cancel reservation
- `POST /api/v1/reservations/{id}/validate` - Validate reservation (owner scans)
- `POST /api/v1/reservations/{id}/check-in` - Check-in with validation code
- `GET /api/v1/reservations/soonest` - Find soonest available slot

#### Credits
- `GET /api/v1/credits/balance` - Get user credit balance
- `POST /api/v1/credits/purchase` - Purchase credits
- `GET /api/v1/credits/transactions` - Get transaction history

#### Reviews
- `POST /api/v1/reviews` - Create review
- `GET /api/v1/reviews/establishment/{id}` - Get establishment reviews

### Frontend (Next.js) Routes

#### Public Routes
- `/` - Homepage with search
- `/establishments` - Browse establishments
- `/establishments/[id]` - Establishment detail page
- `/establishments/[id]/reserve` - Reservation flow
- `/login` - Login page
- `/register` - Registration page

#### Protected Routes (Customers)
- `/dashboard` - User dashboard
- `/reservations` - My reservations
- `/reservations/[id]` - Reservation details
- `/credits` - Credits management
- `/profile` - User profile

#### Protected Routes (Owners)
- `/owner/dashboard` - Owner dashboard
- `/owner/establishments` - Manage establishments
- `/owner/establishments/[id]` - Establishment management
- `/owner/reservations` - View reservations
- `/owner/scan` - QR code scanner

#### Special Routes
- `/validate/[code]` - Validation page (from QR scan)

## Core Workflows

### 1. User Registration & Credits
1. User registers (email/password or OAuth)
2. System creates account with 10 free coffee credits
3. User can purchase more credits

### 2. Find & Reserve Space
1. User searches for establishments (by location or soonest available)
2. User selects establishment and views available spaces
3. System shows real-time availability for selected time slot
4. User confirms reservation (deducts credits)
5. System generates 6-digit validation code
6. User receives confirmation

### 3. Check-in Process
1. User arrives at establishment
2. Owner scans QR code on table/room OR user shows validation code
3. System validates reservation (time window, user, space)
4. Reservation status changes to "checked_in"
5. User can use the space

### 4. Owner Management
1. Owner registers and creates establishment
2. Owner adds spaces and prints QR codes
3. Owner receives reservation notifications
4. Owner can scan QR codes to validate check-ins
5. Owner views analytics dashboard

### 5. Credit System
- Initial signup: 10 credits
- Reservation cost: 1-5 credits (based on duration/space)
- Cancellation: Full refund if >2 hours before, 50% if >30 min, none otherwise
- Purchase: Packages (10, 25, 50, 100 credits)

## Security Considerations

### Authentication
- JWT tokens with refresh mechanism
- Supabase Auth for user management
- Role-based access control (RBAC)

### QR Code Security
- Unique UUID for each space
- Validation codes expire after check-in window
- Server-side validation only
- Rate limiting on validation endpoints

### Data Protection
- Row Level Security (RLS) in Supabase
- Encrypted connections (HTTPS)
- Input validation and sanitization
- SQL injection prevention (parameterized queries)

### Payment Security
- If real payments: PCI compliance
- For symbolic credits: audit trail in credit_transactions

## Real-time Features

### Using Supabase Realtime
- Live availability updates
- Reservation notifications for owners
- Check-in status updates

### WebSocket Connections
- Frontend subscribes to:
  - `reservations:user_id=X` - user's reservations
  - `reservations:establishment_id=Y` - owner's establishment reservations
  - `spaces:establishment_id=Y` - space availability updates

## QR Code Implementation

### Generation
- Each space gets a unique QR code on creation
- QR contains URL: `https://librework.app/validate/{space_id}`
- Generated using Python library (qrcode)
- Stored in Supabase Storage

### Scanning
- Owner app uses device camera
- Scans QR code → extracts space_id
- Prompts for validation code or shows pending reservations
- Validates and checks in user

## Geospatial Features

### Nearest Establishments
- PostGIS extension in Supabase
- Calculate distance using haversine formula
- Sort by distance from user location
- Filter by radius (e.g., within 5km)

### Soonest Available
- Query across all establishments
- Find next available slot for any space
- Consider user location for ranking
- Return top 10 soonest options

## Performance Optimizations

### Backend
- Connection pooling for database
- Redis caching for hot data (establishment details, availability)
- Async/await for I/O operations
- Background tasks for notifications

### Frontend
- Next.js ISR for establishment listings
- Client-side caching with React Query
- Optimistic UI updates
- Image optimization with Next.js Image

### Database
- Proper indexing (see schema section)
- Materialized views for complex queries
- Partition reservations table by date

## Monitoring & Observability

### Metrics
- API response times
- Error rates
- Reservation conversion rates
- Credit transaction volumes
- Space utilization rates

### Logging
- Structured logging (JSON)
- Request/response logging
- Error tracking (Sentry)
- Audit logs for sensitive operations

### Alerts
- High error rates
- Database connection issues
- Failed payments
- Suspicious activity (fraud detection)

## Deployment Strategy

### Environment Setup
- Development: Local Supabase, local FastAPI
- Staging: Supabase staging, Railway staging
- Production: Supabase prod, Railway/Vercel prod

### CI/CD Pipeline
1. Push to GitHub
2. Run tests (pytest for backend, Jest for frontend)
3. Run linters (black, eslint)
4. Build Docker images
5. Deploy to staging
6. Run E2E tests
7. Manual approval for production
8. Deploy to production

### Database Migrations
- Use Supabase migrations
- Version controlled SQL files
- Automatic migration on deploy (staging)
- Manual migration review for production

## Future Enhancements

### Phase 2 Features
- Mobile apps (React Native)
- Push notifications
- Loyalty programs
- Social features (friends, sharing)
- Advanced analytics for owners

### Phase 3 Features
- AI-powered recommendations
- Dynamic pricing based on demand
- Integration with calendar apps
- Group reservations
- Waitlist functionality

## Development Guidelines

### Code Structure
```
librework/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── hooks/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   └── next.config.js
├── supabase/
│   ├── migrations/
│   └── seed.sql
└── docs/
    ├── API.md
    └── DEPLOYMENT.md
```

### Coding Standards
- Python: Black formatter, type hints, docstrings
- TypeScript: ESLint, Prettier, strict mode
- Git: Conventional commits
- Testing: >80% coverage target

### Documentation
- API documentation with OpenAPI/Swagger
- Component documentation with Storybook
- Architecture Decision Records (ADRs)
- Deployment runbooks

