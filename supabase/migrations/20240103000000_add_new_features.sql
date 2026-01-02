-- ============================================================================
-- NEW FEATURES MIGRATION
-- Adds support for: Favorites, Groups, Rewards, Activity Tracking, Notifications
-- ============================================================================

-- ============================================================================
-- 1. USER FAVORITES
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, establishment_id)
);

CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_establishment ON user_favorites(establishment_id);

-- RLS Policies for user_favorites
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own favorites" ON user_favorites;
CREATE POLICY "Users can view their own favorites"
    ON user_favorites FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can add their own favorites" ON user_favorites;
CREATE POLICY "Users can add their own favorites"
    ON user_favorites FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can remove their own favorites" ON user_favorites;
CREATE POLICY "Users can remove their own favorites"
    ON user_favorites FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================================
-- 2. GROUP RESERVATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS reservation_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    space_id UUID NOT NULL REFERENCES spaces(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    total_credits INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES reservation_groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credits_share INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'invited', -- invited, accepted, declined
    joined_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_reservation_groups_creator ON reservation_groups(creator_id);
CREATE INDEX IF NOT EXISTS idx_reservation_groups_space ON reservation_groups(space_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);

-- RLS for groups
ALTER TABLE reservation_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view groups they're in" ON reservation_groups;
CREATE POLICY "Users can view groups they're in"
    ON reservation_groups FOR SELECT
    USING (
        creator_id = auth.uid() OR
        EXISTS (SELECT 1 FROM group_members WHERE group_id = id AND user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Users can create groups" ON reservation_groups;
CREATE POLICY "Users can create groups"
    ON reservation_groups FOR INSERT
    WITH CHECK (creator_id = auth.uid());

DROP POLICY IF EXISTS "Members can view their memberships" ON group_members;
CREATE POLICY "Members can view their memberships"
    ON group_members FOR SELECT
    USING (user_id = auth.uid() OR EXISTS (SELECT 1 FROM reservation_groups WHERE id = group_id AND creator_id = auth.uid()));

DROP POLICY IF EXISTS "Creators can add members" ON group_members;
CREATE POLICY "Creators can add members"
    ON group_members FOR INSERT
    WITH CHECK (EXISTS (SELECT 1 FROM reservation_groups WHERE id = group_id AND creator_id = auth.uid()));


-- ============================================================================
-- 3. LOYALTY & REWARDS PROGRAM
-- ============================================================================

CREATE TABLE IF NOT EXISTS loyalty_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    min_points INTEGER NOT NULL,
    max_points INTEGER,
    credits_bonus_percentage INTEGER DEFAULT 0,
    discount_percentage INTEGER DEFAULT 0,
    perks JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_loyalty (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER DEFAULT 0,
    tier_id UUID REFERENCES loyalty_tiers(id),
    lifetime_reservations INTEGER DEFAULT 0,
    lifetime_credits_spent INTEGER DEFAULT 0,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loyalty_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    transaction_type VARCHAR(100) NOT NULL, -- earned, redeemed, bonus
    description TEXT,
    reference_id UUID, -- reservation_id or other reference
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_loyalty_user ON user_loyalty(user_id);
CREATE INDEX IF NOT EXISTS idx_user_loyalty_tier ON user_loyalty(tier_id);
CREATE INDEX IF NOT EXISTS idx_loyalty_transactions_user ON loyalty_transactions(user_id);

-- Insert default loyalty tiers
INSERT INTO loyalty_tiers (name, min_points, max_points, credits_bonus_percentage, discount_percentage, perks) VALUES
('Bronze', 0, 999, 0, 0, '[]'::jsonb),
('Silver', 1000, 2499, 5, 5, '["Priority Support", "Early Access"]'::jsonb),
('Gold', 2500, 4999, 10, 10, '["Priority Support", "Early Access", "Free Cancellation"]'::jsonb),
('Platinum', 5000, NULL, 15, 15, '["Priority Support", "Early Access", "Free Cancellation", "VIP Lounge Access"]'::jsonb)
ON CONFLICT (name) DO NOTHING;

-- RLS for loyalty
ALTER TABLE user_loyalty ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own loyalty status" ON user_loyalty;
CREATE POLICY "Users can view their own loyalty status"
    ON user_loyalty FOR SELECT
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can view their loyalty transactions" ON loyalty_transactions;
CREATE POLICY "Users can view their loyalty transactions"
    ON loyalty_transactions FOR SELECT
    USING (user_id = auth.uid());


-- ============================================================================
-- 4. PUSH NOTIFICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    device_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, endpoint)
);

CREATE TABLE IF NOT EXISTS notification_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, failed
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_queue_user ON notification_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_queue_status ON notification_queue(status);

-- RLS for push subscriptions
ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_queue ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their push subscriptions" ON push_subscriptions;
CREATE POLICY "Users can manage their push subscriptions"
    ON push_subscriptions FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can view their notifications" ON notification_queue;
CREATE POLICY "Users can view their notifications"
    ON notification_queue FOR SELECT
    USING (user_id = auth.uid());


-- ============================================================================
-- 5. ACTIVITY TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL, -- check_in, reservation, review, etc.
    activity_timestamp TIMESTAMPTZ NOT NULL,
    establishment_id UUID REFERENCES establishments(id) ON DELETE SET NULL,
    reservation_id UUID REFERENCES reservations(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_log_user ON user_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON user_activity_log(activity_timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_log_type ON user_activity_log(activity_type);

-- RLS for activity log
ALTER TABLE user_activity_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their activity" ON user_activity_log;
CREATE POLICY "Users can view their activity"
    ON user_activity_log FOR SELECT
    USING (user_id = auth.uid());


-- ============================================================================
-- 6. EMAIL NOTIFICATION SETTINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_reservations BOOLEAN DEFAULT TRUE,
    email_cancellations BOOLEAN DEFAULT TRUE,
    email_reminders BOOLEAN DEFAULT TRUE,
    email_promotions BOOLEAN DEFAULT FALSE,
    push_reservations BOOLEAN DEFAULT TRUE,
    push_reminders BOOLEAN DEFAULT TRUE,
    reminder_hours_before INTEGER DEFAULT 2,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for notification preferences
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage their notification preferences" ON notification_preferences;
CREATE POLICY "Users can manage their notification preferences"
    ON notification_preferences FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================================
-- 7. TRIGGERS
-- ============================================================================

-- Auto-create loyalty record for new users
CREATE OR REPLACE FUNCTION create_user_loyalty()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_loyalty (user_id, tier_id)
    SELECT NEW.id, id FROM loyalty_tiers WHERE name = 'Bronze' LIMIT 1;
    
    INSERT INTO notification_preferences (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_user_created_loyalty ON users;
CREATE TRIGGER on_user_created_loyalty
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_user_loyalty();


-- Update loyalty points after reservation
CREATE OR REPLACE FUNCTION update_loyalty_after_reservation()
RETURNS TRIGGER AS $$
DECLARE
    points_to_add INTEGER;
BEGIN
    IF NEW.status = 'confirmed' AND (OLD.status IS NULL OR OLD.status != 'confirmed') THEN
        -- Award points based on credits spent (1 point per credit)
        points_to_add := NEW.total_credits;
        
        -- Update user loyalty
        UPDATE user_loyalty
        SET 
            points = points + points_to_add,
            lifetime_reservations = lifetime_reservations + 1,
            lifetime_credits_spent = lifetime_credits_spent + NEW.total_credits,
            updated_at = NOW()
        WHERE user_id = NEW.user_id;
        
        -- Log loyalty transaction
        INSERT INTO loyalty_transactions (user_id, points, transaction_type, description, reference_id)
        VALUES (NEW.user_id, points_to_add, 'earned', 'Points earned from reservation', NEW.id);
        
        -- Log activity
        INSERT INTO user_activity_log (user_id, activity_type, activity_timestamp, establishment_id, reservation_id)
        VALUES (NEW.user_id, 'reservation', NEW.start_time, NEW.establishment_id, NEW.id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_reservation_confirmed ON reservations;
CREATE TRIGGER on_reservation_confirmed
    AFTER INSERT OR UPDATE ON reservations
    FOR EACH ROW
    EXECUTE FUNCTION update_loyalty_after_reservation();


-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
-- All new features database schema created successfully!

