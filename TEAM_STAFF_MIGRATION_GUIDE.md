# Team Staff Table Migration Guide

## Problem
The `/team-profile` command fails with error: `relation "team_staff" does not exist`

## Solution
Create the `team_staff` table in your PostgreSQL database.

---

## Option 1: Run Python Migration Script (Recommended)

### Prerequisites
- Python 3.10+
- `asyncpg` package installed
- `.env` file with correct `DATABASE_URL`

### Steps

1. **Update your `.env` file** with the correct database credentials:
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database
   ```

2. **Run the migration script**:
   ```bash
   python migrations/add_team_staff.py
   ```

3. **Verify success** - You should see:
   ```
   ✅ team_staff table created!
   ✅ Indexes created!
   🎉 Migration complete!
   ```

---

## Option 2: Run SQL File on Remote Server

### For Remote PostgreSQL Database (e.g., Render, Railway, Supabase)

#### Method A: Using psql Command Line

1. **Connect to your database**:
   ```bash
   psql "postgresql://username:password@host:port/database"
   ```

2. **Run the SQL file**:
   ```sql
   \i create_team_staff_table.sql
   ```
   
   OR copy-paste the entire content of `create_team_staff_table.sql`

#### Method B: Using Database Web Interface (Render, Supabase, etc.)

1. **Login to your database dashboard**
2. **Open SQL Query Editor**
3. **Copy the content of `create_team_staff_table.sql`**
4. **Paste and Execute**

#### Method C: Using pgAdmin

1. **Connect to your remote database**
2. **Right-click on your database → Query Tool**
3. **Open `create_team_staff_table.sql`** (File → Open)
4. **Click Execute (F5)**

---

## What This Migration Does

1. ✅ Creates `team_staff` table with columns:
   - `id` (primary key)
   - `team_id` (references teams.id)
   - `coach_id` (references players.discord_id)
   - `manager_1_id` (references players.discord_id)
   - `manager_2_id` (references players.discord_id)
   - `created_at`, `updated_at` (timestamps)

2. ✅ Creates indexes for fast lookups

3. ✅ Migrates existing data from `teams` table (if old columns exist)

4. ✅ Removes old columns from `teams` table (manager_1_id, manager_2_id, coach_id)

5. ✅ Adds trigger to auto-update `updated_at` timestamp

---

## Verify Migration Success

Run this SQL query to verify:

```sql
-- Check if table exists
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'team_staff'
);

-- Count rows
SELECT COUNT(*) FROM team_staff;

-- View table structure
\d team_staff
```

---

## Testing After Migration

1. **Restart your Discord bot**
2. **Run `/team-profile` command**
3. **Should now work without errors!**

---

## Troubleshooting

### Error: "password authentication failed"
- Check your `.env` file has correct `DATABASE_URL`
- Verify username and password are correct
- Make sure database URL format is: `postgresql://user:password@host:port/database`

### Error: "relation already exists"
- Table already exists, migration not needed
- Run this to verify: `SELECT COUNT(*) FROM team_staff;`

### Error: "permission denied"
- Your database user needs CREATE TABLE permissions
- Contact your database admin or use a superuser account

---

## For Render.com Users

1. Go to your Render Dashboard
2. Click on your PostgreSQL database
3. Click "Connect" → Copy the External Database URL
4. Update `.env` with this URL
5. Run: `python migrations/add_team_staff.py`

---

## For Railway.app Users

1. Go to your Railway project
2. Click on PostgreSQL service
3. Copy the Database URL from Variables
4. Update `.env` with this URL
5. Run: `python migrations/add_team_staff.py`

---

## For Supabase Users

1. Go to Project Settings → Database
2. Copy Connection String (URI mode)
3. Replace `[YOUR-PASSWORD]` with actual password
4. Update `.env` with this URL
5. Run: `python migrations/add_team_staff.py`

---

## Need Help?

If migration fails, check:
1. Database credentials are correct
2. Database is accessible (not behind firewall)
3. Python packages are installed: `pip install asyncpg python-dotenv`
4. You have sufficient database permissions
