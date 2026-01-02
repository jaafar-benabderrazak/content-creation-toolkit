-- ============================================================================
-- LibreWork Database Schema for Replit/Supabase
-- Complete schema in ONE file - run this in Supabase SQL Editor
-- ============================================================================

-- Enable PostGIS extension for geography type
CREATE EXTENSION IF NOT EXISTS postgis;

-- Clean start (be careful in production!)
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS spaces CASCADE;
DROP TABLE IF EXISTS establishments CASCADE;
DROP TABLE IF EXISTS credit_transactions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS reservation_status CASCADE;
DROP TYPE IF EXISTS transaction_type CASCADE;

-- ============================================================================
-- TYPES
-- ============================================================================

CREATE TYPE user_role AS ENUM ('customer', 'owner', 'admin');
CREATE TYPE reservation_status AS ENUM ('pending', 'confirmed', 'cancelled', 'completed');
CREATE TYPE transaction_type AS ENUM ('purchase', 'reservation', 'refund', 'cancellation');

-- ============================================================================
-- USERS TABLE (No foreign key to auth.users!)
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'customer',
    coffee_credits INTEGER NOT NULL DEFAULT 0,
    phone_number TEXT,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- CREDIT TRANSACTIONS
-- ============================================================================

CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type transaction_type NOT NULL,
    description TEXT,
    reservation_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_created_at ON credit_transactions(created_at DESC);

-- ============================================================================
-- ESTABLISHMENTS
-- ============================================================================

CREATE TABLE establishments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    postal_code TEXT,
    country TEXT DEFAULT 'France',
    location GEOGRAPHY(POINT),
    phone TEXT,
    email TEXT,
    website TEXT,
    opening_hours JSONB,
    amenities TEXT[],
    services TEXT[],
    images TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_establishments_owner_id ON establishments(owner_id);
CREATE INDEX idx_establishments_city ON establishments(city);
CREATE INDEX idx_establishments_is_active ON establishments(is_active);
CREATE INDEX idx_establishments_location ON establishments USING GIST(location);

-- ============================================================================
-- SPACES
-- ============================================================================

CREATE TABLE spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    space_type TEXT NOT NULL,
    capacity INTEGER,
    credit_price_per_hour INTEGER NOT NULL DEFAULT 1,
    amenities TEXT[],
    images TEXT[],
    is_available BOOLEAN DEFAULT true,
    qr_code_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_spaces_establishment_id ON spaces(establishment_id);
CREATE INDEX idx_spaces_is_available ON spaces(is_available);

-- ============================================================================
-- RESERVATIONS
-- ============================================================================

CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    space_id UUID NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status reservation_status NOT NULL DEFAULT 'pending',
    total_credits INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_end_after_start CHECK (end_time > start_time)
);

CREATE INDEX idx_reservations_user_id ON reservations(user_id);
CREATE INDEX idx_reservations_space_id ON reservations(space_id);
CREATE INDEX idx_reservations_start_time ON reservations(start_time);
CREATE INDEX idx_reservations_status ON reservations(status);

-- ============================================================================
-- REVIEWS
-- ============================================================================

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, establishment_id, reservation_id)
);

CREATE INDEX idx_reviews_establishment_id ON reviews(establishment_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE establishments ENABLE ROW LEVEL SECURITY;
ALTER TABLE spaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Anyone can register" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can view all profiles" ON users FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- Credit transactions policies
CREATE POLICY "Users can view own transactions" ON credit_transactions FOR SELECT USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "System can create transactions" ON credit_transactions FOR INSERT WITH CHECK (true);

-- Establishments policies
CREATE POLICY "Anyone can view active establishments" ON establishments FOR SELECT USING (is_active = true OR owner_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "Owners can create establishments" ON establishments FOR INSERT WITH CHECK (owner_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "Owners can update own establishments" ON establishments FOR UPDATE USING (owner_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- Spaces policies
CREATE POLICY "Anyone can view available spaces" ON spaces FOR SELECT USING (true);
CREATE POLICY "Owners can manage spaces" ON spaces FOR ALL USING (
    establishment_id IN (
        SELECT id FROM establishments WHERE owner_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid
    )
);

-- Reservations policies
CREATE POLICY "Users can view own reservations" ON reservations FOR SELECT USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "Users can create reservations" ON reservations FOR INSERT WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "Users can update own reservations" ON reservations FOR UPDATE USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- Reviews policies
CREATE POLICY "Anyone can view reviews" ON reviews FOR SELECT USING (true);
CREATE POLICY "Users can create reviews" ON reviews FOR INSERT WITH CHECK (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "Users can update own reviews" ON reviews FOR UPDATE USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
CREATE POLICY "Users can delete own reviews" ON reviews FOR DELETE USING (user_id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);

-- ============================================================================
-- DEMO DATA (Optional - for testing)
-- ============================================================================

-- Note: Run these INSERTs separately AFTER you've registered your first user via the app

/*
-- Example: After registering as owner1@gmail.com via the app, get the user_id and insert demo data:

INSERT INTO establishments (id, owner_id, name, description, address, city, services)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'YOUR_USER_ID_HERE',  -- Replace with actual user ID from registration
    'Demo Café',
    'A cozy workspace café',
    '123 Main St',
    'Paris',
    ARRAY['wifi', 'coffee', 'quiet_spaces']
);

INSERT INTO spaces (establishment_id, name, space_type, capacity, credit_price_per_hour)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'Table 1',
    'desk',
    1,
    2
);
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these to verify everything is set up correctly:

-- Check all tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check users table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Verify password_hash column exists
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'password_hash'
        ) THEN '✅ password_hash column exists'
        ELSE '❌ password_hash column MISSING'
    END as status;

-- ✅ LibreWork database schema created successfully!

