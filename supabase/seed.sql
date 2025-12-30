-- Seed data for development and testing
-- Note: This assumes you have created test users via Supabase Auth UI
-- Replace these UUIDs with actual user IDs from your auth.users table

-- Insert sample establishments (using placeholder owner IDs)
-- In production, you'll need to replace these with actual user IDs

-- Sample data for establishments
INSERT INTO establishments (id, owner_id, name, description, address, city, latitude, longitude, category, opening_hours, images, amenities, is_active)
VALUES
    (
        '11111111-1111-1111-1111-111111111111',
        '00000000-0000-0000-0000-000000000001', -- Replace with actual owner ID
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
        TRUE
    );

-- Insert spaces for Café Central
INSERT INTO spaces (id, establishment_id, name, space_type, capacity, qr_code, is_available)
VALUES
    ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Table 1', 'table', 2, 'QR-CAFE-TABLE-001', TRUE),
    ('a1111111-1111-1111-1111-111111111112', '11111111-1111-1111-1111-111111111111', 'Table 2', 'table', 4, 'QR-CAFE-TABLE-002', TRUE),
    ('a1111111-1111-1111-1111-111111111113', '11111111-1111-1111-1111-111111111111', 'Table 3', 'table', 2, 'QR-CAFE-TABLE-003', TRUE),
    ('a1111111-1111-1111-1111-111111111114', '11111111-1111-1111-1111-111111111111', 'Corner Booth', 'booth', 4, 'QR-CAFE-BOOTH-001', TRUE),
    ('a1111111-1111-1111-1111-111111111115', '11111111-1111-1111-1111-111111111111', 'Window Seat', 'table', 1, 'QR-CAFE-WINDOW-001', TRUE);

-- Insert spaces for Bibliothèque Moderne
INSERT INTO spaces (id, establishment_id, name, space_type, capacity, qr_code, is_available)
VALUES
    ('b2222222-2222-2222-2222-222222222221', '22222222-2222-2222-2222-222222222222', 'Study Room A', 'room', 4, 'QR-LIB-ROOM-A', TRUE),
    ('b2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'Study Room B', 'room', 6, 'QR-LIB-ROOM-B', TRUE),
    ('b2222222-2222-2222-2222-222222222223', '22222222-2222-2222-2222-222222222222', 'Desk 1', 'desk', 1, 'QR-LIB-DESK-001', TRUE),
    ('b2222222-2222-2222-2222-222222222224', '22222222-2222-2222-2222-222222222222', 'Desk 2', 'desk', 1, 'QR-LIB-DESK-002', TRUE),
    ('b2222222-2222-2222-2222-222222222225', '22222222-2222-2222-2222-222222222222', 'Desk 3', 'desk', 1, 'QR-LIB-DESK-003', TRUE);

-- Insert spaces for WorkHub Coworking
INSERT INTO spaces (id, establishment_id, name, space_type, capacity, qr_code, is_available)
VALUES
    ('c3333333-3333-3333-3333-333333333331', '33333333-3333-3333-3333-333333333333', 'Meeting Room 1', 'room', 8, 'QR-WORK-MEET-001', TRUE),
    ('c3333333-3333-3333-3333-333333333332', '33333333-3333-3333-3333-333333333333', 'Meeting Room 2', 'room', 4, 'QR-WORK-MEET-002', TRUE),
    ('c3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'Hot Desk 1', 'desk', 1, 'QR-WORK-DESK-001', TRUE),
    ('c3333333-3333-3333-3333-333333333334', '33333333-3333-3333-3333-333333333333', 'Hot Desk 2', 'desk', 1, 'QR-WORK-DESK-002', TRUE),
    ('c3333333-3333-3333-3333-333333333335', '33333333-3333-3333-3333-333333333333', 'Hot Desk 3', 'desk', 1, 'QR-WORK-DESK-003', TRUE);

-- Note: Sample reservations and reviews would need actual user IDs
-- These would be created through the application during testing

-- Helper query to verify spatial indexing is working
-- SELECT name, city, ST_Distance(location, ST_SetSRID(ST_MakePoint(2.3522, 48.8566), 4326)::geography) / 1000 AS distance_km
-- FROM establishments
-- ORDER BY distance_km;

