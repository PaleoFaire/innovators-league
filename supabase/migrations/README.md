# Supabase Migrations

This folder holds SQL migrations that need to be run once against the
production Supabase project to enable features in the app.

Each migration is idempotent — safe to re-run. Just paste the whole file
into the Supabase SQL editor and hit **Run**.

## How to apply a migration

1. Open https://supabase.com/dashboard/project/imxrdesbozbxmlffewyr (or
   whichever project `auth.js` points at).
2. Left nav → **SQL Editor** → **New query**.
3. Open the `.sql` file for the migration you want to run, copy its full
   contents, paste into the editor.
4. Click **Run**. You should see a green "Success. No rows returned"
   banner at the bottom.
5. Optional: go to **Table Editor** and confirm the new table appears.

## Migrations, newest first

### `20260422_company_votes.sql` — Community Upvotes
Creates `public.company_votes` + the `public.company_vote_counts` view and
the three RLS policies (read-for-all, insert-own, delete-own).

**Powers:** the upvote button on every company card / modal / profile
page, the "🔥 Community Picks" sort option on the main grid, the
`TILVotes` client-side module.

**Before running this migration**, the upvote button and sort option
silently render nothing (votes.js detects the missing view and returns
early). So there's no rush — you can ship the code and apply the
migration whenever you're ready to flip the feature on.

After running it, no code deploy is needed — users start seeing the
button immediately on next page load.
