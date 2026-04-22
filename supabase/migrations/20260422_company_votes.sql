-- ═══════════════════════════════════════════════════════════════════════════
-- The Innovators League — Community Upvote Feature
-- ═══════════════════════════════════════════════════════════════════════════
-- Run ONCE in your Supabase SQL editor. Idempotent — safe to re-run.
--
-- Adds a `company_votes` table so logged-in users can upvote companies.
-- Row-Level Security ensures:
--   • Anyone (including anon) can READ aggregate vote counts
--   • Users can only INSERT or DELETE their OWN votes
--   • Users can never modify another user's votes
--
-- The primary key (user_id, company_name) enforces one-vote-per-user-per-company
-- automatically — duplicate inserts are rejected by the DB.
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Create the table
create table if not exists public.company_votes (
  user_id      uuid references auth.users(id) on delete cascade not null,
  company_name text not null,
  voted_at     timestamptz not null default now(),
  primary key (user_id, company_name)
);

-- 2. Index for fast aggregate queries (group by company_name)
create index if not exists idx_company_votes_name
  on public.company_votes (company_name);

create index if not exists idx_company_votes_user
  on public.company_votes (user_id, voted_at desc);

-- 3. Enable Row-Level Security
alter table public.company_votes enable row level security;

-- 4. Public read — anyone can query vote counts (drives the count badge on cards)
drop policy if exists "Anyone can read votes" on public.company_votes;
create policy "Anyone can read votes"
  on public.company_votes for select
  to anon, authenticated
  using (true);

-- 5. Insert — users can only add votes in their own name
drop policy if exists "Users can cast their own vote" on public.company_votes;
create policy "Users can cast their own vote"
  on public.company_votes for insert
  to authenticated
  with check (user_id = auth.uid());

-- 6. Delete — users can only remove their own vote (used for toggle-off)
drop policy if exists "Users can remove their own vote" on public.company_votes;
create policy "Users can remove their own vote"
  on public.company_votes for delete
  to authenticated
  using (user_id = auth.uid());

-- 7. Aggregate view — one query gets every company's vote count.
--    The client calls `from('company_vote_counts').select('*')` instead of
--    running a group-by on the base table, which would be slow at scale.
create or replace view public.company_vote_counts as
  select
    company_name,
    count(*)::int            as vote_count,
    max(voted_at)            as last_voted_at
  from public.company_votes
  group by company_name;

grant select on public.company_vote_counts to anon, authenticated;

-- ═══════════════════════════════════════════════════════════════════════════
-- Done. votes.js will work automatically once this runs. No server-side code
-- needed — Supabase + RLS handle everything.
-- ═══════════════════════════════════════════════════════════════════════════
