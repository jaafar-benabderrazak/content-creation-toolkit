-- Seed data for development and testing
-- This script creates sample establishments and spaces

-- IMPORTANT: This seed file requires users to be created first
-- You have two options:

-- Option 1: Create users manually in Supabase Dashboard
-- 1. Go to Authentication > Users
-- 2. Create 3 users:
--    - owner1@test.com (password: test123456)
--    - owner2@test.com (password: test123456)  
--    - customer@test.com (password: test123456)
-- 3. Note their UUIDs
-- 4. Run this script, replacing the UUIDs below with the actual ones

-- Option 2: Skip seed data and create establishments through the API
-- Just register users through your application and they'll get profiles automatically

-- For demo purposes, you can use these placeholder UUIDs
-- But you MUST first create corresponding users in Supabase Auth
-- Replace these with actual user IDs from auth.users table:
DO $$
DECLARE
    owner_id_1 UUID := '00000000-0000-0000-0000-000000000001';
    owner_id_2 UUID := '00000000-0000-0000-0000-000000000002';
    customer_id UUID := '00000000-0000-0000-0000-000000000003';
    user_exists BOOLEAN;
BEGIN
    -- Check if users exist in auth.users (they need to be created first)
    SELECT EXISTS(SELECT 1 FROM auth.users WHERE id = owner_id_1) INTO user_exists;
    
    IF NOT user_exists THEN
        RAISE NOTICE 'Users not found in auth.users table!';
        RAISE NOTICE 'Please create users first:';
        RAISE NOTICE '1. Go to Supabase Dashboard > Authentication > Users';
        RAISE NOTICE '2. Click "Invite User" or "Add User"';
        RAISE NOTICE '3. Create: owner1@test.com, owner2@test.com, customer@test.com';
        RAISE NOTICE '4. Set metadata: {"role": "owner"} for owners, {"role": "customer"} for customer';
        RAISE NOTICE '5. Note their UUIDs and update this seed file';
        RAISE NOTICE '';
        RAISE NOTICE 'Alternatively, register users through your application and skip seed data.';
        RAISE EXCEPTION 'Cannot seed without users in auth.users table';
    END IF;
END $$;

-- Note: In production, users should be created via Supabase Auth UI or API
-- These test users won't have passwords and are for seeding data only
-- To actually login, create real users through the application

-- Step 2: Insert sample establishments
-- Step 2: Insert sample establishments
INSERT INTO establishments (id, owner_id, name, description, address, city, latitude, longitude, category, opening_hours, images, amenities, services, is_active)
VALUES
    (
        '11111111-1111-1111-1111-111111111111',
        '00000000-0000-0000-0000-000000000001',
        'Café Central',
        'A cozy cafe in the heart of the city with great coffee and a quiet atmosphere perfect for working.',
        '123 Main Street',
        'Paris',
        48.8566,
        2.3522,
        'cafe',
        '{
            "monday": {"open": "08:00", "close": "20:00"},
            "tuesday": {"open": "08:00", "close": "20:00"},
            "wednesday": {"open": "08:00", "close": "20:00"},
            "thursday": {"open": "08:00", "close": "20:00"},
            "friday": {"open": "08:00", "close": "22:00"},
            "saturday": {"open": "09:00", "close": "22:00"},
            "sunday": {"open": "09:00", "close": "18:00"}
        }',
        ARRAY['https://images.unsplash.com/photo-1554118811-1e0d58224f24'],
        ARRAY['wifi', 'power_outlets', 'quiet', 'food', 'drinks'],
        ARRAY['WiFi', 'Coffee & Beverages', 'Power Outlets', 'Air Conditioning'],
        TRUE
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        '00000000-0000-0000-0000-000000000001',
        'Bibliothèque Moderne',
        'Modern library with private study rooms and collaborative spaces.',
        '456 Library Avenue',
        'Paris',
        48.8606,
        2.3376,
        'library',
        '{
            "monday": {"open": "09:00", "close": "21:00"},
            "tuesday": {"open": "09:00", "close": "21:00"},
            "wednesday": {"open": "09:00", "close": "21:00"},
            "thursday": {"open": "09:00", "close": "21:00"},
            "friday": {"open": "09:00", "close": "19:00"},
            "saturday": {"open": "10:00", "close": "18:00"},
            "sunday": {"open": "10:00", "close": "18:00"}
        }',
        ARRAY['https://images.unsplash.com/photo-1521587760476-6c12a4b040da'],
        ARRAY['wifi', 'power_outlets', 'quiet'],
        ARRAY['WiFi', 'Quiet Study Areas', 'Printing & Scanning', 'Lockers'],
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        '00000000-0000-0000-0000-000000000002',
        'WorkHub Coworking',
        'Professional coworking space with meeting rooms and hot desks.',
        '789 Business Boulevard',
        'Lyon',
        45.7640,
        4.8357,
        'coworking',
        '{
            "monday": {"open": "07:00", "close": "22:00"},
            "tuesday": {"open": "07:00", "close": "22:00"},
            "wednesday": {"open": "07:00", "close": "22:00"},
            "thursday": {"open": "07:00", "close": "22:00"},
            "friday": {"open": "07:00", "close": "20:00"},
            "saturday": {"open": "09:00", "close": "17:00"},
            "sunday": {"open": "closed", "close": "closed"}
        }',
        ARRAY['https://images.unsplash.com/photo-1497366216548-37526070297c'],
        ARRAY['wifi', 'power_outlets', 'food', 'drinks'],
        ARRAY['WiFi', 'Meeting Rooms', 'Coffee & Beverages', 'Parking', '24/7 Access'],
        TRUE
    );

-- Step 3: Insert spaces for establishments
-- Insert spaces for Café Central
INSERT INTO spaces (id, establishment_id, name, description, space_type, capacity, credit_price_per_hour, qr_code, is_available)
VALUES
    ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Table 1', 'Cozy table by the window', 'table', 2, 1, 'QR-CAFE-TABLE-001', TRUE),
    ('a1111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', 'Table 2', 'Large communal table', 'table', 4, 1, 'QR-CAFE-TABLE-002', TRUE),
    ('a1111111-1111-1111-1111-111111111113', '11111111-1111-1111-1111-111111111111', 'Table 3', 'Quiet corner table', 'table', 2, 1, 'QR-CAFE-TABLE-003', TRUE),
    ('a1111111-1111-1111-1111-111111111114', '11111111-1111-1111-1111-111111111111', 'Corner Booth', 'Private booth with seating for 4', 'booth', 4, 2, 'QR-CAFE-BOOTH-001', TRUE),
    ('a1111111-1111-1111-1111-111111111115', '11111111-1111-1111-1111-111111111111', 'Window Seat', 'Single seat with great view', 'table', 1, 1, 'QR-CAFE-WINDOW-001', TRUE);

-- Insert spaces for Bibliothèque Moderne
INSERT INTO spaces (id, establishment_id, name, description, space_type, capacity, credit_price_per_hour, qr_code, is_available)
VALUES
    ('b2222222-2222-2222-2222-222222222221', '22222222-2222-2222-2222-222222222222', 'Study Room A', 'Private study room with whiteboard', 'room', 4, 3, 'QR-LIB-ROOM-A', TRUE),
    ('b2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'Study Room B', 'Larger study room for groups', 'room', 6, 4, 'QR-LIB-ROOM-B', TRUE),
    ('b2222222-2222-2222-2222-222222222223', '22222222-2222-2222-2222-222222222222', 'Desk 1', 'Individual study desk', 'desk', 1, 1, 'QR-LIB-DESK-001', TRUE),
    ('b2222222-2222-2222-2222-222222222224', '22222222-2222-2222-2222-222222222222', 'Desk 2', 'Individual study desk', 'desk', 1, 1, 'QR-LIB-DESK-002', TRUE),
    ('b2222222-2222-2222-2222-222222222225', '22222222-2222-2222-2222-222222222222', 'Desk 3', 'Individual study desk', 'desk', 1, 1, 'QR-LIB-DESK-003', TRUE);

-- Insert spaces for WorkHub Coworking
INSERT INTO spaces (id, establishment_id, name, description, space_type, capacity, credit_price_per_hour, qr_code, is_available)
VALUES
    ('c3333333-3333-3333-3333-333333333331', '33333333-3333-3333-3333-333333333333', 'Meeting Room 1', 'Large meeting room with projector', 'room', 8, 5, 'QR-WORK-MEET-001', TRUE),
    ('c3333333-3333-3333-3333-333333333332', '33333333-3333-3333-3333-333333333333', 'Meeting Room 2', 'Small meeting room for teams', 'room', 4, 3, 'QR-WORK-MEET-002', TRUE),
    ('c3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'Hot Desk 1', 'Flexible hot desk space', 'desk', 1, 2, 'QR-WORK-DESK-001', TRUE),
    ('c3333333-3333-3333-3333-333333333334', '33333333-3333-3333-3333-333333333333', 'Hot Desk 2', 'Flexible hot desk space', 'desk', 1, 2, 'QR-WORK-DESK-002', TRUE),
    ('c3333333-3333-3333-3333-333333333335', '33333333-3333-3333-3333-333333333333', 'Hot Desk 3', 'Flexible hot desk space', 'desk', 1, 2, 'QR-WORK-DESK-003', TRUE);

-- Step 4: Verify data
-- Note: Sample reservations and reviews require authentication
-- These should be created through the application after users login

-- Test accounts created:
-- 1. owner1@test.com (Owner) - Owns Café Central and Bibliothèque Moderne
-- 2. owner2@test.com (Owner) - Owns WorkHub Coworking
-- 3. customer@test.com (Customer) - Can make reservations

-- Important: These users don't have passwords and exist only in the users table
-- To actually use them, you need to:
-- 1. Create real accounts via Supabase Auth or the application
-- 2. Update the owner_id in establishments to match real user IDs
-- OR just use this seed data for demonstration and create new establishments

-- Verification queries:
-- SELECT * FROM users;
-- SELECT name, city, category FROM establishments;
-- SELECT e.name as establishment, s.name as space, s.credit_price_per_hour 
-- FROM spaces s JOIN establishments e ON s.establishment_id = e.id;

