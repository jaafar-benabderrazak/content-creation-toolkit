-- Add new columns to users table for enhanced profile features
-- Run this after the initial schema and RLS migrations

-- Add phone_number column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS phone_number TEXT;

-- Add avatar_url column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Add preferences column (JSONB for flexible user preferences)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb;

-- Add services column to establishments (if not already added)
ALTER TABLE establishments 
ADD COLUMN IF NOT EXISTS services TEXT[] DEFAULT '{}';

-- Add description and credit_price_per_hour to spaces
ALTER TABLE spaces 
ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE spaces 
ADD COLUMN IF NOT EXISTS credit_price_per_hour INTEGER DEFAULT 1 CHECK (credit_price_per_hour > 0);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Update the trigger function to handle new fields (optional metadata)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, role, coffee_credits, phone_number, avatar_url, preferences)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
        COALESCE((NEW.raw_user_meta_data->>'role')::user_role, 'customer'),
        10, -- Initial bonus credits
        NEW.raw_user_meta_data->>'phone_number',
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE(NEW.raw_user_meta_data->'preferences', '{}'::jsonb)
    );
    
    -- Record the initial credit transaction
    INSERT INTO public.credit_transactions (user_id, amount, transaction_type, description)
    VALUES (NEW.id, 10, 'bonus', 'Welcome bonus - 10 free coffee credits');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant permissions on new columns
GRANT SELECT, UPDATE ON users TO authenticated;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'New columns added:';
    RAISE NOTICE '- users.phone_number (TEXT)';
    RAISE NOTICE '- users.avatar_url (TEXT)';
    RAISE NOTICE '- users.preferences (JSONB)';
    RAISE NOTICE '- establishments.services (TEXT[])';
    RAISE NOTICE '- spaces.description (TEXT)';
    RAISE NOTICE '- spaces.credit_price_per_hour (INTEGER)';
    RAISE NOTICE '';
    RAISE NOTICE 'Trigger updated to handle new fields.';
    RAISE NOTICE 'You can now register users with all profile features!';
    RAISE NOTICE '=================================================================';
END $$;

