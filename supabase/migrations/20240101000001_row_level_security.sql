-- Enable Row Level Security on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE establishments ENABLE ROW LEVEL SECURITY;
ALTER TABLE spaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Establishments policies
CREATE POLICY "Anyone can view active establishments"
    ON establishments FOR SELECT
    USING (is_active = TRUE OR owner_id = auth.uid());

CREATE POLICY "Owners can create establishments"
    ON establishments FOR INSERT
    WITH CHECK (
        auth.uid() = owner_id 
        AND EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Owners can update their own establishments"
    ON establishments FOR UPDATE
    USING (auth.uid() = owner_id)
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Owners can delete their own establishments"
    ON establishments FOR DELETE
    USING (auth.uid() = owner_id);

-- Spaces policies
CREATE POLICY "Anyone can view spaces of active establishments"
    ON spaces FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = spaces.establishment_id 
            AND (is_active = TRUE OR owner_id = auth.uid())
        )
    );

CREATE POLICY "Owners can create spaces in their establishments"
    ON spaces FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = establishment_id 
            AND owner_id = auth.uid()
        )
    );

CREATE POLICY "Owners can update spaces in their establishments"
    ON spaces FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = establishment_id 
            AND owner_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = establishment_id 
            AND owner_id = auth.uid()
        )
    );

CREATE POLICY "Owners can delete spaces in their establishments"
    ON spaces FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = establishment_id 
            AND owner_id = auth.uid()
        )
    );

-- Reservations policies
CREATE POLICY "Users can view their own reservations"
    ON reservations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Owners can view reservations for their establishments"
    ON reservations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = reservations.establishment_id 
            AND owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can create reservations"
    ON reservations FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND coffee_credits >= cost_credits
        )
        AND check_space_availability(space_id, start_time, end_time)
    );

CREATE POLICY "Users can update their own pending reservations"
    ON reservations FOR UPDATE
    USING (
        auth.uid() = user_id 
        AND status IN ('pending', 'confirmed')
    )
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Owners can update reservations for their establishments"
    ON reservations FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = reservations.establishment_id 
            AND owner_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM establishments 
            WHERE id = reservations.establishment_id 
            AND owner_id = auth.uid()
        )
    );

-- Credit transactions policies
CREATE POLICY "Users can view their own transactions"
    ON credit_transactions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "System can create transactions"
    ON credit_transactions FOR INSERT
    WITH CHECK (TRUE); -- Will be created by triggers/backend only

-- Reviews policies
CREATE POLICY "Anyone can view reviews"
    ON reviews FOR SELECT
    USING (TRUE);

CREATE POLICY "Users can create reviews for their completed reservations"
    ON reviews FOR INSERT
    WITH CHECK (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM reservations 
            WHERE id = reservation_id 
            AND user_id = auth.uid()
            AND status = 'completed'
        )
    );

CREATE POLICY "Users can update their own reviews"
    ON reviews FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reviews"
    ON reviews FOR DELETE
    USING (auth.uid() = user_id);

-- Create function to automatically create user profile on auth signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, role, coffee_credits)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
        COALESCE((NEW.raw_user_meta_data->>'role')::user_role, 'customer'),
        10 -- Initial bonus credits
    );
    
    -- Record the initial credit transaction
    INSERT INTO public.credit_transactions (user_id, amount, transaction_type, description)
    VALUES (NEW.id, 10, 'bonus', 'Welcome bonus - 10 free coffee credits');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

