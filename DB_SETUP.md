# VALM Tournament Bot - Database Setup

This document explains how to set up the PostgreSQL database for the VALM tournament bot.

## Prerequisites

- PostgreSQL 12 or later
- Python 3.8 or later
- `asyncpg` Python package (included in requirements.txt)

## Installation Steps

1. Install PostgreSQL if not already installed
2. Create a new database:
   ```sql
   CREATE DATABASE valorant_mobile;
   ```

3. Add the database URL to your `.env` file:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/valorant_mobile
   ```
   
   For the default local setup with no password:
   ```env
   DATABASE_URL=postgresql://postgres@localhost:5432/valorant_mobile
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the database initialization script:
   ```bash
   python scripts/init_db.py
   ```

This will:
- Create all necessary tables
- Set up indexes for performance
- Add triggers for timestamp management
- Migrate existing data from JSON files if present

## Database Schema

The database uses two main tables:

### Players Table
Stores core player information:
- `discord_id`: Primary key, unique Discord user ID
- `ign`: In-game name (unique)
- `player_id`: Numeric in-game ID (unique)
- `region`: Player's region
- `created_at`: Timestamp of registration
- `updated_at`: Last update timestamp

### Player Stats Table
Stores player statistics per tournament:
- `id`: Unique record ID
- `player_id`: References players(discord_id)
- `tournament_id`: Tournament identifier
- `kills`, `deaths`, `assists`: Combat statistics
- `matches_played`: Total matches
- `wins`, `losses`: Match outcomes
- `mvps`: Number of MVP awards
- `created_at`, `updated_at`: Timestamps

## Indexes
- Case-insensitive IGN lookup: `idx_players_ign_lower`
- Leaderboard queries: `idx_player_stats_score`

## Score Calculation

Player scores are calculated using the following weights:
- Kill: 100 points
- Assist: 50 points
- Death: -50 points
- Win: 500 points
- Match participation: 100 points

Requirements:
- Minimum 3 matches played to be ranked
- Score cannot be negative