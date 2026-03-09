-- ============================================================
-- Weekly Intelligence Brief: Database Schema
-- Run in Supabase SQL Editor:
--   https://supabase.com/dashboard/project/imxrdesbozbxmlffewyr/sql/new
-- ============================================================

-- Step 1: Alert preferences table (stores user opt-in settings)
CREATE TABLE IF NOT EXISTS alert_preferences (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  categories JSONB DEFAULT '[]'::jsonb,
  priority_threshold TEXT DEFAULT 'medium',
  email_enabled BOOLEAN DEFAULT false,
  email_frequency TEXT DEFAULT 'weekly',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Email send log (prevents duplicate sends, tracks delivery)
CREATE TABLE IF NOT EXISTS email_send_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  brief_date DATE NOT NULL,
  sent_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT NOT NULL DEFAULT 'sent',  -- sent, failed, bounced
  resend_id TEXT,                        -- Resend API message ID
  sections_included TEXT[],              -- which sections were in this brief
  UNIQUE(user_id, brief_date)            -- prevent double-sends
);

-- Step 3: Row-level security for alert_preferences
ALTER TABLE alert_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own preferences" ON alert_preferences
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences" ON alert_preferences
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON alert_preferences
  FOR UPDATE USING (auth.uid() = user_id);

-- Service role can read all (for weekly brief Edge Function)
CREATE POLICY "Service role can read all preferences" ON alert_preferences
  FOR SELECT USING (auth.role() = 'service_role');

-- Step 4: Row-level security for email_send_log
ALTER TABLE email_send_log ENABLE ROW LEVEL SECURITY;

-- Users can see their own send history
CREATE POLICY "Users can read own send log" ON email_send_log
  FOR SELECT USING (auth.uid() = user_id);

-- Only service role can insert (Edge Function sends emails)
CREATE POLICY "Service role can insert send log" ON email_send_log
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can read send log" ON email_send_log
  FOR SELECT USING (auth.role() = 'service_role');

-- Step 5: Indexes
CREATE INDEX IF NOT EXISTS email_send_log_user_idx ON email_send_log(user_id);
CREATE INDEX IF NOT EXISTS email_send_log_date_idx ON email_send_log(brief_date);
CREATE INDEX IF NOT EXISTS alert_preferences_email_idx ON alert_preferences(email_enabled) WHERE email_enabled = true;
