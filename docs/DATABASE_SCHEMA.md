# LibreWork Database Schema

## Overview
LibreWork uses Supabase (PostgreSQL) as its database backend with Row Level Security (RLS) policies for data protection.

## Tables

### users
Stores user profile information.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  phone_number TEXT,
  avatar_url TEXT,
  role TEXT NOT NULL CHECK (role IN ('customer', 'owner', 'admin')),
  coffee_credits INTEGER DEFAULT 10,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### establishments
Stores cafe, library, and coworking space information.

```sql
CREATE TABLE establishments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  address TEXT NOT NULL,
  city TEXT NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('cafe', 'library', 'coworking', 'restaurant')),
  opening_hours JSONB NOT NULL,
  amenities TEXT[] DEFAULT '{}',
  services TEXT[] DEFAULT '{}',  -- WiFi, Coffee, Printing, Meeting Rooms, etc.
  images TEXT[] DEFAULT '{}',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_establishments_owner ON establishments(owner_id);
CREATE INDEX idx_establishments_city ON establishments(city);
CREATE INDEX idx_establishments_category ON establishments(category);
CREATE INDEX idx_establishments_location ON establishments USING GIST (ll_to_earth(latitude, longitude));
```

### spaces
Stores individual spaces (tables, rooms, desks) within establishments.

```sql
CREATE TABLE spaces (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  space_type TEXT NOT NULL CHECK (space_type IN ('table', 'room', 'desk', 'booth')),
  capacity INTEGER NOT NULL CHECK (capacity > 0),
  credit_price_per_hour INTEGER NOT NULL DEFAULT 1 CHECK (credit_price_per_hour > 0),
  qr_code TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(8), 'hex'),
  qr_code_image_url TEXT,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_spaces_establishment ON spaces(establishment_id);
CREATE UNIQUE INDEX idx_spaces_qr_code ON spaces(qr_code);
```

### reservations
Stores booking information.

```sql
CREATE TABLE reservations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  space_id UUID NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
  establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'checked_in', 'completed', 'cancelled')),
  cost_credits INTEGER NOT NULL,
  validation_code TEXT UNIQUE NOT NULL DEFAULT substring(encode(gen_random_bytes(4), 'hex'), 1, 6),
  checked_in_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

CREATE INDEX idx_reservations_user ON reservations(user_id);
CREATE INDEX idx_reservations_space ON reservations(space_id);
CREATE INDEX idx_reservations_establishment ON reservations(establishment_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_reservations_time ON reservations(start_time, end_time);
```

### credit_transactions
Stores credit purchase and usage history.

```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,
  transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'reservation', 'cancellation_refund', 'bonus')),
  reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_user ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_type ON credit_transactions(transaction_type);
```

### reviews
Stores customer reviews for establishments.

```sql
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
  reservation_id UUID NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, reservation_id)
);

CREATE INDEX idx_reviews_establishment ON reviews(establishment_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
```

## Key Features

### QR Code System
- **Generation**: Each space automatically gets a unique QR code on creation
- **Validation**: Customers scan QR codes to validate reservations or make new bookings
- **Printing**: Owners can download printable QR codes with space details via `/api/v1/spaces/{space_id}/qr-code/print`

### Credit System
- **Initial Credits**: New users receive 10 free credits
- **Pricing**: Each space can have a custom credit price per hour (configurable by owner)
- **Transactions**: All credit movements are tracked in `credit_transactions`
- **Refunds**: Cancellation refunds based on time before reservation:
  - Full refund: 2+ hours before
  - 50% refund: 30 minutes - 2 hours before
  - No refund: Less than 30 minutes before

### User Roles
- **Customer**: Can browse, reserve spaces, and leave reviews
- **Owner**: Can manage establishments, spaces, view analytics, and handle reservations
- **Admin**: Full system access (future feature)

### Services & Amenities
Establishments can list available services:
- WiFi
- Coffee/Beverages
- Printing/Scanning
- Meeting Rooms
- Lockers
- Power Outlets
- Air Conditioning
- Parking
- And more...

## Row Level Security (RLS) Policies

### Users Table
- Users can view their own profile
- Users can update their own profile
- Public can view basic info (name, avatar) of other users

### Establishments Table
- Anyone can view active establishments
- Owners can create, update, and delete their own establishments
- Admins have full access

### Spaces Table
- Anyone can view available spaces
- Owners can manage spaces in their establishments

### Reservations Table
- Users can view their own reservations
- Owners can view reservations for their establishments
- Users can create reservations for available spaces
- Users can cancel their own pending/confirmed reservations

### Reviews Table
- Anyone can read reviews
- Users can create reviews for their completed reservations
- Users can update/delete their own reviews

## Triggers

### update_updated_at_timestamp
Updates the `updated_at` column on row modifications for relevant tables.

### create_user_profile
Automatically creates a user profile in the `users` table when a new auth user is created.

### handle_reservation_credits
Deducts credits when a reservation is confirmed and adds a credit transaction record.

### handle_cancellation_refund
Calculates and processes refunds when a reservation is cancelled based on time until start.

## Indexes
Strategic indexes are created for:
- Foreign key relationships
- Frequently queried fields (status, dates, location)
- Unique constraints (QR codes, validation codes)
- Full-text search (future feature)

## Future Enhancements
- Full-text search for establishments
- PostGIS for advanced geospatial queries
- Real-time notifications using Supabase Realtime
- File storage integration for establishment images
- Payment gateway integration for credit purchases

