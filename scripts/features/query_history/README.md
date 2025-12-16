# Query History Feature

## Overview

Query History is an **optional feature** that tracks user search queries and allows favorites. It's designed to be easily enabled/disabled without affecting core functionality.

## Features

- ✅ **Query History**: Automatically saves all user searches
- ✅ **Favorites**: Mark frequently used queries as favorites
- ✅ **Recent Searches**: Quick access to last N searches
- ✅ **Autocomplete**: Suggestions based on query history
- ✅ **Popular Queries**: Discover common searches

## Installation

### Step 1: Run Database Migration

```bash
python scripts/features/query_history/migrations/run_migration.py
```

This creates the necessary database tables.

### Step 2: Enable Feature

Add to your `.env` file:

```env
ENABLE_QUERY_HISTORY=true
```

### Step 3: Restart API Server

The feature will be automatically loaded when the server starts.

## Usage

### Frontend

The feature is automatically integrated into the frontend. Users will see:
- A history button (📜) in the top-right corner
- Recent queries panel
- Favorites panel
- Autocomplete suggestions while typing

### API Endpoints

All endpoints are under `/api/query-history/`:

- `GET /api/query-history/recent?user_id=...&limit=10` - Get recent queries
- `GET /api/query-history/favorites?user_id=...` - Get favorites
- `POST /api/query-history/save` - Save a query
- `POST /api/query-history/favorite/{query_id}` - Toggle favorite
- `GET /api/query-history/suggestions?user_id=...&prefix=...` - Get suggestions
- `GET /api/query-history/popular?limit=10` - Get popular queries

## Disabling the Feature

### Option 1: Environment Variable

Set in `.env`:
```env
ENABLE_QUERY_HISTORY=false
```

### Option 2: Remove from Frontend

Remove from `api/frontend/index.html`:
- Remove `<script src="query-history.js"></script>`
- Remove query history HTML elements

### Option 3: Remove from Backend

In `api/app.py`, the router is conditionally loaded. If `ENABLE_QUERY_HISTORY=false`, it won't load.

## Rollback

To completely remove the feature:

```bash
# Run rollback script
psql -h localhost -p 5433 -U postgres -d ai_requests_db -f scripts/features/query_history/migrations/001_rollback_query_history_tables.sql
```

**Warning**: This will delete all query history data!

## Architecture

The feature is modular and non-breaking:

- **Service**: `scripts/features/query_history/service.py` - Core logic
- **API Routes**: `api/routes/query_history.py` - API endpoints
- **Frontend**: `api/frontend/query-history.js` - UI logic
- **Database**: Separate tables that can be dropped independently

## Non-Breaking Design

- ✅ Queries are saved **after** search completes (doesn't block search)
- ✅ If history fails, search still works
- ✅ Feature can be disabled without code changes
- ✅ No dependencies on core search logic
- ✅ Graceful degradation if tables don't exist

## Troubleshooting

### Feature not working?

1. Check if enabled: `ENABLE_QUERY_HISTORY=true` in `.env`
2. Check if tables exist: Run migration script
3. Check API logs for errors
4. Check browser console for frontend errors

### Performance issues?

- Query history is saved asynchronously (non-blocking)
- If slow, check database indexes
- Consider limiting history per user

## Future Enhancements

- User authentication (currently uses session ID)
- Export query history
- Query analytics
- Share queries between users

