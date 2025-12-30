-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create custom types
CREATE TYPE user_role AS ENUM ('customer', 'owner', 'admin');
CREATE TYPE establishment_category AS ENUM ('cafe', 'library', 'coworking', 'restaurant');
CREATE TYPE space_type AS ENUM ('table', 'room', 'desk', 'booth');
CREATE TYPE reservation_status AS ENUM ('pending', 'confirmed', 'checked_in', 'completed', 'cancelled');
CREATE TYPE transaction_type AS ENUM ('purchase', 'reservation', 'cancellation_refund', 'bonus');

-- Users table (extends Supabase auth.users)
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role user_role DEFAULT 'customer' NOT NULL,
    coffee_credits INTEGER DEFAULT 10 NOT NULL CHECK (coffee_credits >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Establishments table
CREATE TABLE establishments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location GEOGRAPHY(POINT, 4326), -- PostGIS point for spatial queries
    category establishment_category NOT NULL,
    opening_hours JSONB NOT NULL DEFAULT '{}', -- {monday: {open: "09:00", close: "18:00"}, ...}
    images TEXT[] DEFAULT '{}',
    amenities TEXT[] DEFAULT '{}', -- ['wifi', 'power_outlets', 'quiet', 'food', 'drinks']
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Spaces table
CREATE TABLE spaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    space_type space_type NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    qr_code TEXT UNIQUE NOT NULL DEFAULT uuid_generate_v4()::TEXT,
    qr_code_image_url TEXT,
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(establishment_id, name)
);

-- Reservations table
CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    space_id UUID NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status reservation_status DEFAULT 'pending' NOT NULL,
    cost_credits INTEGER NOT NULL CHECK (cost_credits > 0),
    validation_code TEXT NOT NULL, -- 6-digit code
    checked_in_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CHECK (end_time > start_time),
    CHECK (start_time >= created_at)
);

-- Credit transactions table
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL, -- positive for credit, negative for debit
    transaction_type transaction_type NOT NULL,
    reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Reviews table
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    reservation_id UUID NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, reservation_id) -- One review per reservation
);

-- Create indexes for performance
CREATE INDEX idx_establishments_location ON establishments USING GIST(location);
CREATE INDEX idx_establishments_city ON establishments(city);
CREATE INDEX idx_establishments_category ON establishments(category);
CREATE INDEX idx_establishments_owner ON establishments(owner_id);
CREATE INDEX idx_establishments_active ON establishments(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_spaces_establishment ON spaces(establishment_id);
CREATE INDEX idx_spaces_available ON spaces(is_available) WHERE is_available = TRUE;
CREATE INDEX idx_spaces_qr_code ON spaces(qr_code);

CREATE INDEX idx_reservations_user ON reservations(user_id);
CREATE INDEX idx_reservations_space ON reservations(space_id);
CREATE INDEX idx_reservations_establishment ON reservations(establishment_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_reservations_time_range ON reservations(start_time, end_time);
CREATE INDEX idx_reservations_validation_code ON reservations(validation_code);

CREATE INDEX idx_credit_transactions_user ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_type ON credit_transactions(transaction_type);

CREATE INDEX idx_reviews_establishment ON reviews(establishment_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_establishments_updated_at BEFORE UPDATE ON establishments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spaces_updated_at BEFORE UPDATE ON spaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reservations_updated_at BEFORE UPDATE ON reservations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update establishment location point from lat/lng
CREATE OR REPLACE FUNCTION update_establishment_location()
RETURNS TRIGGER AS $$
BEGIN
    NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically set location
CREATE TRIGGER set_establishment_location
BEFORE INSERT OR UPDATE OF latitude, longitude ON establishments
FOR EACH ROW EXECUTE FUNCTION update_establishment_location();

-- Function to generate 6-digit validation code
CREATE OR REPLACE FUNCTION generate_validation_code()
RETURNS TEXT AS $$
BEGIN
    RETURN LPAD(FLOOR(RANDOM() * 1000000)::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- Trigger to generate validation code for reservations
CREATE OR REPLACE FUNCTION set_reservation_validation_code()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.validation_code IS NULL OR NEW.validation_code = '' THEN
        NEW.validation_code = generate_validation_code();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_reservation_validation_code
BEFORE INSERT ON reservations
FOR EACH ROW EXECUTE FUNCTION set_reservation_validation_code();

-- Function to check space availability (no overlapping reservations)
CREATE OR REPLACE FUNCTION check_space_availability(
    p_space_id UUID,
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE,
    p_exclude_reservation_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    overlap_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO overlap_count
    FROM reservations
    WHERE space_id = p_space_id
        AND status IN ('pending', 'confirmed', 'checked_in')
        AND (p_exclude_reservation_id IS NULL OR id != p_exclude_reservation_id)
        AND (
            (start_time <= p_start_time AND end_time > p_start_time)
            OR (start_time < p_end_time AND end_time >= p_end_time)
            OR (start_time >= p_start_time AND end_time <= p_end_time)
        );
    
    RETURN overlap_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate reservation cost based on duration
CREATE OR REPLACE FUNCTION calculate_reservation_cost(
    p_start_time TIMESTAMP WITH TIME ZONE,
    p_end_time TIMESTAMP WITH TIME ZONE
)
RETURNS INTEGER AS $$
DECLARE
    duration_hours DECIMAL;
    cost INTEGER;
BEGIN
    duration_hours = EXTRACT(EPOCH FROM (p_end_time - p_start_time)) / 3600.0;
    
    -- Cost calculation: 1 credit per hour, minimum 1, maximum 10
    cost = GREATEST(1, LEAST(10, CEIL(duration_hours)));
    
    RETURN cost;
END;
$$ LANGUAGE plpgsql;

-- Function to handle credit transaction on reservation
CREATE OR REPLACE FUNCTION handle_reservation_credits()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Deduct credits
        UPDATE users
        SET coffee_credits = coffee_credits - NEW.cost_credits
        WHERE id = NEW.user_id;
        
        -- Record transaction
        INSERT INTO credit_transactions (user_id, amount, transaction_type, reservation_id, description)
        VALUES (NEW.user_id, -NEW.cost_credits, 'reservation', NEW.id, 
                'Reservation at ' || (SELECT name FROM establishments WHERE id = NEW.establishment_id));
        
    ELSIF TG_OP = 'UPDATE' AND OLD.status != 'cancelled' AND NEW.status = 'cancelled' THEN
        -- Calculate refund based on cancellation time
        DECLARE
            refund_amount INTEGER;
            time_until_start INTERVAL;
        BEGIN
            time_until_start = NEW.start_time - NOW();
            
            IF time_until_start > INTERVAL '2 hours' THEN
                refund_amount = NEW.cost_credits; -- Full refund
            ELSIF time_until_start > INTERVAL '30 minutes' THEN
                refund_amount = NEW.cost_credits / 2; -- 50% refund
            ELSE
                refund_amount = 0; -- No refund
            END IF;
            
            IF refund_amount > 0 THEN
                -- Refund credits
                UPDATE users
                SET coffee_credits = coffee_credits + refund_amount
                WHERE id = NEW.user_id;
                
                -- Record transaction
                INSERT INTO credit_transactions (user_id, amount, transaction_type, reservation_id, description)
                VALUES (NEW.user_id, refund_amount, 'cancellation_refund', NEW.id, 
                        'Refund for cancelled reservation');
            END IF;
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER manage_reservation_credits
AFTER INSERT OR UPDATE OF status ON reservations
FOR EACH ROW EXECUTE FUNCTION handle_reservation_credits();

