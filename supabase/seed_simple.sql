-- Seed data for development and testing
-- This is a simplified seed file that can be run without pre-existing users

-- RECOMMENDED APPROACH:
-- Instead of seeding, just register users through your application!
-- 1. Start your backend and frontend
-- 2. Register as "owner" role
-- 3. Create establishments through the Owner Dashboard
-- 4. Register as "customer" role  
-- 5. Browse and make reservations

-- However, if you want sample data without users, here's a simpler approach:
-- This seed file is intentionally left minimal.
-- To add seed data with users, follow these steps:

/*
STEP-BY-STEP GUIDE TO ADD SEED DATA:

1. Create users in Supabase Dashboard:
   - Go to Authentication > Users
   - Click "Add User" (or "Invite User")
   - Create:
     * owner1@test.com (password: yourpassword)
       - In User Metadata, add: {"role": "owner", "full_name": "John Owner"}
     * owner2@test.com (password: yourpassword)
       - In User Metadata, add: {"role": "owner", "full_name": "Jane Owner"}
     * customer@test.com (password: yourpassword)
       - In User Metadata, add: {"role": "customer", "full_name": "Test Customer"}

2. After creating users, they will automatically get entries in the users table
   (thanks to the trigger from row_level_security.sql)

3. Get their UUIDs:
   - In Supabase SQL Editor, run:
     SELECT id, email, full_name, role FROM users;
   - Copy the UUIDs

4. Update and run the INSERT statements below with actual UUIDs

5. Run this file in SQL Editor
*/

-- ============================================================================
-- SAMPLE ESTABLISHMENTS (Update UUIDs with your actual user IDs)
-- ============================================================================

-- Uncomment and update these after creating users:

/*
INSERT INTO establishments (id, owner_id, name, description, address, city, latitude, longitude, category, opening_hours, images, amenities, services, is_active)
VALUES
    (
        '11111111-1111-1111-1111-111111111111',
        'YOUR-OWNER-1-UUID-HERE', -- Replace with actual UUID
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
    );

INSERT INTO spaces (id, establishment_id, name, description, space_type, capacity, credit_price_per_hour, qr_code, is_available)
VALUES
    ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Table 1', 'Cozy table by the window', 'table', 2, 1, 'QR-CAFE-TABLE-001', TRUE),
    ('a1111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', 'Table 2', 'Large communal table', 'table', 4, 1, 'QR-CAFE-TABLE-002', TRUE),
    ('a1111111-1111-1111-1111-111111111113', '11111111-1111-1111-1111-111111111111', 'Corner Booth', 'Private booth with seating for 4', 'booth', 4, 2, 'QR-CAFE-BOOTH-001', TRUE);
*/

-- ============================================================================
-- VERIFICATION QUERIES (run these to check your data)
-- ============================================================================

-- Check if users were created by the trigger:
-- SELECT id, email, full_name, role, coffee_credits FROM users;

-- Check establishments:
-- SELECT id, name, city, category FROM establishments;

-- Check spaces:
-- SELECT s.name, s.space_type, s.credit_price_per_hour, e.name as establishment
-- FROM spaces s
-- JOIN establishments e ON s.establishment_id = e.id;

-- ============================================================================
-- ALTERNATIVE: Quick test without seed data
-- ============================================================================

-- Just run your application and:
-- 1. Register as owner (role: owner)
-- 2. Create establishment via Owner Dashboard
-- 3. Add spaces and generate QR codes
-- 4. Register as customer and test reservations

RAISE NOTICE '=================================================================';
RAISE NOTICE 'Seed file loaded successfully!';
RAISE NOTICE '';
RAISE NOTICE 'To add sample data:';
RAISE NOTICE '1. Create users in Supabase Dashboard > Authentication > Users';
RAISE NOTICE '2. Get their UUIDs from: SELECT id, email FROM users;';
RAISE NOTICE '3. Uncomment and update the INSERT statements in this file';
RAISE NOTICE '4. Run this file again';
RAISE NOTICE '';
RAISE NOTICE 'OR simply register users through your application!';
RAISE NOTICE '=================================================================';

