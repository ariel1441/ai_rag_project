# Query History Storage - How It Works

## Current Implementation

### Storage Location
Query history is stored in **PostgreSQL database** in the following tables:
- `user_query_history` - Main table storing all queries
- `query_statistics` - Aggregate statistics (optional)

### User Identification
Currently uses **localStorage** in the browser to generate a user ID:
- First visit: Creates `user_<timestamp>` (e.g., `user_1765788010719`)
- Stored in: `localStorage.getItem('queryHistory_userId')`
- Persists across browser sessions (until localStorage is cleared)

### How It Works Now

1. **User opens website** → Browser checks localStorage for user ID
2. **If no ID exists** → Creates new user ID and stores it
3. **User performs search** → Query is saved to database with this user ID
4. **User returns later** → Same user ID is used (from localStorage)
5. **All queries with same user ID** → Show up in "חיפושים אחרונים" and "חיפושים מועדפים"

### Persistence
- ✅ **Survives API server restart** - Data is in database, not memory
- ✅ **Survives browser close** - localStorage persists
- ❌ **Lost if localStorage cleared** - User gets new ID
- ❌ **Not per actual user** - Multiple people on same browser share history

## Future Implementation (Per-User)

### Option 1: User Authentication
```python
# When user logs in
user_id = current_user.email  # or user.id

# Save query with authenticated user ID
history_service.save_query(
    user_id=user_id,  # Real user identifier
    query_text=query,
    ...
)
```

### Option 2: Session-Based
```python
# Use session ID from API
user_id = request.session.get('user_id')

# Or from JWT token
user_id = jwt.decode(token)['user_id']
```

### Option 3: API Key Based
```python
# Each user has API key
user_id = get_user_from_api_key(api_key)
```

## Database Schema

```sql
CREATE TABLE user_query_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,  -- Currently: localStorage ID, Future: real user ID
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),  -- 'search', 'rag-no-llm', 'rag-full'
    intent VARCHAR(50),  -- 'person', 'project', 'general', etc.
    entities JSONB,  -- Store parsed entities
    result_count INTEGER,
    execution_time_ms INTEGER,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1
);
```

## Migration Path (Current → Future)

### Step 1: Keep Current System
- Continue using localStorage IDs
- Works for single-user scenarios

### Step 2: Add User Authentication
- When user logs in, migrate localStorage ID to real user ID
- Or link localStorage ID to user account

### Step 3: Full Migration
- All queries use real user IDs
- localStorage ID becomes optional (for anonymous users)

## Current Limitations

1. **Not per actual user** - Multiple people on same browser share history
2. **Lost if localStorage cleared** - User gets new ID, loses history
3. **No user authentication** - Can't distinguish between real users

## Benefits of Current System

1. ✅ **No setup required** - Works immediately
2. ✅ **No authentication needed** - Good for internal tools
3. ✅ **Persistent** - Survives server restarts
4. ✅ **Fast** - No authentication overhead

## When to Upgrade

Upgrade to per-user system when:
- Multiple users need separate histories
- Need to track usage per user
- Need to share queries between devices
- Need user authentication anyway

## Summary

**Now:**
- Uses localStorage-generated user ID
- Stored in PostgreSQL database
- Persists across server restarts
- Not per actual user (browser-based)

**Future:**
- Use real user authentication
- Each user has separate history
- Can sync across devices
- Better for multi-user scenarios

