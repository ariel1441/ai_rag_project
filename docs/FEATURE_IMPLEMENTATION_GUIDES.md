# Feature Implementation Guides
## Detailed Implementation Plans for High-Priority Features

**Last Updated:** Current Session  
**Purpose:** Step-by-step implementation guides for selected features

---

## 📋 Table of Contents

1. [Query History & Favorites](#1-query-history--favorites)
2. [Advanced Filters UI](#2-advanced-filters-ui)
3. [Dashboard & Analytics](#3-dashboard--analytics)

---

## 1. Query History & Favorites

### 📖 Feature Description

**What it does:**
- **Query History:** Saves all user searches automatically, allowing users to quickly re-run previous queries
- **Favorites:** Users can mark frequently used queries as favorites for one-click access
- **Recent Searches:** Shows last N searches in dropdown/autocomplete
- **Query Suggestions:** Autocomplete based on history

**User Benefits:**
- ✅ No need to retype common queries
- ✅ Faster access to frequently used searches
- ✅ Discover what others are searching
- ✅ Learn from past successful queries

**Use Cases:**
- Worker searches "פניות מאור גלילי" daily → saves as favorite
- Manager runs same report weekly → clicks favorite instead of typing
- User forgets exact query → checks history
- New user → sees popular queries to learn system

---

### 🎯 User Stories

1. **As a worker**, I want to see my recent searches so I can quickly re-run them
2. **As a manager**, I want to save my common queries as favorites so I can access them with one click
3. **As a user**, I want autocomplete suggestions based on my history so I can type faster
4. **As an admin**, I want to see popular queries so I can understand what users need

---

### 🗄️ Database Schema

**New Table: `user_query_history`**

```sql
CREATE TABLE user_query_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,  -- Could be email, username, or session ID
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),  -- 'search', 'rag-no-llm', 'rag-full'
    intent VARCHAR(50),  -- 'person', 'project', 'general', etc.
    entities JSONB,  -- Store parsed entities
    result_count INTEGER,  -- How many results were returned
    execution_time_ms INTEGER,  -- How long it took
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1  -- How many times this query was used
);

-- Indexes for fast lookups
CREATE INDEX idx_user_query_history_user_id ON user_query_history(user_id);
CREATE INDEX idx_user_query_history_last_used ON user_query_history(user_id, last_used_at DESC);
CREATE INDEX idx_user_query_history_favorites ON user_query_history(user_id, is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX idx_user_query_history_text ON user_query_history USING gin(to_tsvector('hebrew', query_text));  -- For text search

-- Popular queries (aggregate table, updated periodically)
CREATE TABLE query_statistics (
    query_text TEXT PRIMARY KEY,
    total_uses INTEGER DEFAULT 1,
    unique_users INTEGER DEFAULT 1,
    avg_result_count NUMERIC,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 🔌 API Endpoints

**File:** `api/routes/query_history.py` (new file)

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from api.models import QueryHistoryItem, QueryHistoryResponse

router = APIRouter(prefix="/api/query-history", tags=["query-history"])

@router.get("/recent", response_model=List[QueryHistoryItem])
async def get_recent_queries(
    user_id: str,
    limit: int = 10
):
    """
    Get recent queries for a user.
    Returns last N queries ordered by last_used_at.
    """
    # Implementation in services.py
    pass

@router.get("/favorites", response_model=List[QueryHistoryItem])
async def get_favorite_queries(user_id: str):
    """
    Get all favorite queries for a user.
    """
    pass

@router.post("/save")
async def save_query(
    user_id: str,
    query_text: str,
    query_type: str,
    intent: Optional[str] = None,
    entities: Optional[dict] = None,
    result_count: Optional[int] = None,
    execution_time_ms: Optional[int] = None
):
    """
    Save a query to history.
    If query already exists for user, update last_used_at and increment use_count.
    """
    pass

@router.post("/favorite/{query_id}")
async def toggle_favorite(query_id: int, user_id: str):
    """
    Toggle favorite status for a query.
    """
    pass

@router.delete("/history/{query_id}")
async def delete_query(query_id: int, user_id: str):
    """
    Delete a query from history.
    """
    pass

@router.get("/suggestions", response_model=List[str])
async def get_query_suggestions(
    user_id: str,
    prefix: str,
    limit: int = 5
):
    """
    Get autocomplete suggestions based on user's query history.
    Returns queries that start with prefix, ordered by use_count.
    """
    pass

@router.get("/popular", response_model=List[QueryHistoryItem])
async def get_popular_queries(limit: int = 10):
    """
    Get most popular queries across all users.
    Useful for discovering common searches.
    """
    pass
```

---

### 🛠️ Service Layer Implementation

**File:** `api/services.py` (add to existing file)

```python
class QueryHistoryService:
    """Service for managing query history and favorites."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect_db(self):
        """Connect to database."""
        if self.conn:
            return
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        self.conn = psycopg2.connect(
            host=host, port=int(port), database=database,
            user=user, password=password
        )
        self.cursor = self.conn.cursor()
    
    def save_query(
        self,
        user_id: str,
        query_text: str,
        query_type: str,
        intent: Optional[str] = None,
        entities: Optional[dict] = None,
        result_count: Optional[int] = None,
        execution_time_ms: Optional[int] = None
    ) -> int:
        """
        Save or update query in history.
        Returns query ID.
        """
        if not self.conn:
            self.connect_db()
        
        # Check if query already exists for this user
        self.cursor.execute("""
            SELECT id, use_count FROM user_query_history
            WHERE user_id = %s AND query_text = %s
        """, (user_id, query_text))
        
        existing = self.cursor.fetchone()
        
        if existing:
            # Update existing query
            query_id, current_count = existing
            self.cursor.execute("""
                UPDATE user_query_history
                SET last_used_at = CURRENT_TIMESTAMP,
                    use_count = use_count + 1,
                    result_count = COALESCE(%s, result_count),
                    execution_time_ms = COALESCE(%s, execution_time_ms)
                WHERE id = %s
            """, (result_count, execution_time_ms, query_id))
            self.conn.commit()
            return query_id
        else:
            # Insert new query
            self.cursor.execute("""
                INSERT INTO user_query_history
                (user_id, query_text, query_type, intent, entities, 
                 result_count, execution_time_ms, use_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                RETURNING id
            """, (
                user_id, query_text, query_type, intent,
                json.dumps(entities) if entities else None,
                result_count, execution_time_ms
            ))
            query_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return query_id
    
    def get_recent_queries(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get recent queries for user."""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute("""
            SELECT id, query_text, query_type, intent, result_count,
                   is_favorite, last_used_at, use_count
            FROM user_query_history
            WHERE user_id = %s
            ORDER BY last_used_at DESC
            LIMIT %s
        """, (user_id, limit))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row[0],
                'query_text': row[1],
                'query_type': row[2],
                'intent': row[3],
                'result_count': row[4],
                'is_favorite': row[5],
                'last_used_at': row[6].isoformat() if row[6] else None,
                'use_count': row[7]
            })
        return results
    
    def get_favorite_queries(self, user_id: str) -> List[dict]:
        """Get favorite queries for user."""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute("""
            SELECT id, query_text, query_type, intent, result_count,
                   last_used_at, use_count
            FROM user_query_history
            WHERE user_id = %s AND is_favorite = TRUE
            ORDER BY last_used_at DESC
        """, (user_id,))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row[0],
                'query_text': row[1],
                'query_type': row[2],
                'intent': row[3],
                'result_count': row[4],
                'last_used_at': row[5].isoformat() if row[5] else None,
                'use_count': row[6]
            })
        return results
    
    def toggle_favorite(self, query_id: int, user_id: str) -> bool:
        """Toggle favorite status."""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute("""
            UPDATE user_query_history
            SET is_favorite = NOT is_favorite
            WHERE id = %s AND user_id = %s
            RETURNING is_favorite
        """, (query_id, user_id))
        
        result = self.cursor.fetchone()
        if result:
            self.conn.commit()
            return result[0]
        return False
    
    def get_suggestions(self, user_id: str, prefix: str, limit: int = 5) -> List[str]:
        """Get autocomplete suggestions."""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute("""
            SELECT DISTINCT query_text, MAX(use_count) as max_count
            FROM user_query_history
            WHERE user_id = %s AND query_text ILIKE %s
            GROUP BY query_text
            ORDER BY max_count DESC, query_text
            LIMIT %s
        """, (user_id, f'{prefix}%', limit))
        
        return [row[0] for row in self.cursor.fetchall()]
```

---

### 🎨 Frontend Implementation

**File:** `api/frontend/app.js` (add to existing)

```javascript
// Query History Management
class QueryHistory {
    constructor() {
        this.userId = this.getUserId(); // Get from localStorage or session
        this.recentQueries = [];
        this.favoriteQueries = [];
    }
    
    getUserId() {
        // Simple implementation - use session ID or email
        let userId = localStorage.getItem('userId');
        if (!userId) {
            userId = 'user_' + Date.now();
            localStorage.setItem('userId', userId);
        }
        return userId;
    }
    
    async saveQuery(queryText, queryType, intent, resultCount, executionTime) {
        try {
            const response = await fetch('/api/query-history/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    query_text: queryText,
                    query_type: queryType,
                    intent: intent,
                    result_count: resultCount,
                    execution_time_ms: executionTime
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error saving query:', error);
        }
    }
    
    async loadRecentQueries(limit = 10) {
        try {
            const response = await fetch(
                `/api/query-history/recent?user_id=${this.userId}&limit=${limit}`
            );
            this.recentQueries = await response.json();
            this.renderRecentQueries();
        } catch (error) {
            console.error('Error loading recent queries:', error);
        }
    }
    
    async loadFavoriteQueries() {
        try {
            const response = await fetch(
                `/api/query-history/favorites?user_id=${this.userId}`
            );
            this.favoriteQueries = await response.json();
            this.renderFavoriteQueries();
        } catch (error) {
            console.error('Error loading favorites:', error);
        }
    }
    
    async getSuggestions(prefix) {
        try {
            const response = await fetch(
                `/api/query-history/suggestions?user_id=${this.userId}&prefix=${encodeURIComponent(prefix)}&limit=5`
            );
            return await response.json();
        } catch (error) {
            console.error('Error getting suggestions:', error);
            return [];
        }
    }
    
    renderRecentQueries() {
        const container = document.getElementById('recentQueries');
        if (!container) return;
        
        container.innerHTML = '<h3>חיפושים אחרונים</h3>';
        
        if (this.recentQueries.length === 0) {
            container.innerHTML += '<p>אין חיפושים אחרונים</p>';
            return;
        }
        
        const list = document.createElement('ul');
        this.recentQueries.forEach(query => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="query-text" onclick="queryHistory.runQuery('${query.query_text}', '${query.query_type}')">
                    ${query.query_text}
                </span>
                <span class="query-meta">${query.result_count || 0} תוצאות</span>
                <button onclick="queryHistory.toggleFavorite(${query.id})" class="favorite-btn">
                    ${query.is_favorite ? '★' : '☆'}
                </button>
            `;
            list.appendChild(li);
        });
        container.appendChild(list);
    }
    
    renderFavoriteQueries() {
        const container = document.getElementById('favoriteQueries');
        if (!container) return;
        
        container.innerHTML = '<h3>חיפושים מועדפים</h3>';
        
        if (this.favoriteQueries.length === 0) {
            container.innerHTML += '<p>אין חיפושים מועדפים</p>';
            return;
        }
        
        const list = document.createElement('ul');
        this.favoriteQueries.forEach(query => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="query-text" onclick="queryHistory.runQuery('${query.query_text}', '${query.query_type}')">
                    ${query.query_text}
                </span>
                <button onclick="queryHistory.toggleFavorite(${query.id})" class="favorite-btn">★</button>
            `;
            list.appendChild(li);
        });
        container.appendChild(list);
    }
    
    async toggleFavorite(queryId) {
        try {
            const response = await fetch(`/api/query-history/favorite/${queryId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId })
            });
            await this.loadRecentQueries();
            await this.loadFavoriteQueries();
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }
    
    runQuery(queryText, queryType) {
        // Set input value and trigger search
        document.getElementById('queryInput').value = queryText;
        document.querySelector(`input[value="${queryType}"]`).checked = true;
        performSearch();
    }
}

// Initialize
const queryHistory = new QueryHistory();

// Add autocomplete to search input
const queryInput = document.getElementById('queryInput');
let suggestionsList = null;

queryInput.addEventListener('input', async (e) => {
    const prefix = e.target.value;
    if (prefix.length < 2) {
        if (suggestionsList) suggestionsList.remove();
        return;
    }
    
    const suggestions = await queryHistory.getSuggestions(prefix);
    if (suggestions.length === 0) {
        if (suggestionsList) suggestionsList.remove();
        return;
    }
    
    // Create or update suggestions dropdown
    if (!suggestionsList) {
        suggestionsList = document.createElement('ul');
        suggestionsList.className = 'suggestions-list';
        queryInput.parentElement.appendChild(suggestionsList);
    }
    
    suggestionsList.innerHTML = suggestions.map(s => 
        `<li onclick="queryHistory.runQuery('${s}', 'search')">${s}</li>`
    ).join('');
});

// Save query after search
async function performSearch() {
    // ... existing search code ...
    
    // After search completes:
    const queryText = document.getElementById('queryInput').value;
    const queryType = document.querySelector('input[name="searchType"]:checked').value;
    const intent = data.intent; // From search response
    const resultCount = data.total_found; // From search response
    const executionTime = data.search_time_ms; // From search response
    
    await queryHistory.saveQuery(queryText, queryType, intent, resultCount, executionTime);
    await queryHistory.loadRecentQueries();
}

// Load on page load
document.addEventListener('DOMContentLoaded', () => {
    queryHistory.loadRecentQueries();
    queryHistory.loadFavoriteQueries();
});
```

---

### 📝 Implementation Steps

**Step 1: Database Setup (30 minutes)**
```sql
-- Run the CREATE TABLE statements above
-- Test with sample data
```

**Step 2: Backend API (2-3 hours)**
1. Create `api/routes/query_history.py`
2. Add `QueryHistoryService` to `api/services.py`
3. Register routes in `api/app.py`
4. Test endpoints with Postman/curl

**Step 3: Frontend Integration (2-3 hours)**
1. Add query history UI to `index.html`
2. Add JavaScript functions to `app.js`
3. Integrate with existing search function
4. Style with CSS

**Step 4: Testing (1 hour)**
1. Test saving queries
2. Test favorites
3. Test autocomplete
4. Test recent queries display

**Total Time: ~6-8 hours**

---

## 2. Advanced Filters UI

### 📖 Feature Description

**What it does:**
- **Visual Filter Builder:** Drag-and-drop interface to build complex filters
- **Multi-Select Filters:** Select multiple values for status, type, person, etc.
- **Date Range Picker:** Easy date range selection
- **Saved Filter Presets:** Save and reuse filter combinations
- **Filter Chips:** Visual representation of active filters
- **Quick Filters:** One-click common filters

**User Benefits:**
- ✅ No need to type complex queries
- ✅ Visual interface is more intuitive
- ✅ Combine multiple filters easily
- ✅ Reuse common filter combinations

**Use Cases:**
- Filter by: Status=1 AND Type=4 AND Person="אור גלילי"
- Filter by: Date range (last 30 days) AND Status=10
- Quick filter: "My Requests" (person = current user)
- Quick filter: "Urgent" (status date < 7 days)

---

### 🎯 User Stories

1. **As a worker**, I want to filter by multiple statuses at once so I can see all my active requests
2. **As a manager**, I want to filter by date range and person so I can see someone's recent work
3. **As a user**, I want to save my filter combinations so I don't have to rebuild them
4. **As a user**, I want to see all active filters at a glance so I know what I'm viewing

---

### 🗄️ Database Schema

**New Table: `saved_filters`**

```sql
CREATE TABLE saved_filters (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    filter_name VARCHAR(200) NOT NULL,
    filter_config JSONB NOT NULL,  -- Store filter structure
    is_public BOOLEAN DEFAULT FALSE,  -- Can others use this?
    use_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_saved_filters_user_id ON saved_filters(user_id);
CREATE INDEX idx_saved_filters_public ON saved_filters(is_public) WHERE is_public = TRUE;
```

**Filter Config JSON Structure:**
```json
{
    "filters": [
        {
            "field": "requeststatusid",
            "operator": "in",
            "values": ["1", "2", "3"]
        },
        {
            "field": "requesttypeid",
            "operator": "equals",
            "value": "4"
        },
        {
            "field": "updatedby",
            "operator": "contains",
            "value": "אור גלילי"
        },
        {
            "field": "requeststatusdate",
            "operator": "date_range",
            "start": "2024-01-01",
            "end": "2024-12-31"
        }
    ],
    "logic": "AND"  // or "OR"
}
```

---

### 🔌 API Endpoints

**Add to existing `api/routes/search.py` or create new file:**

```python
@router.post("/api/search/advanced")
async def advanced_search(
    filters: FilterConfig,
    top_k: int = 20,
    include_details: bool = True
):
    """
    Advanced search with multiple filters.
    """
    pass

@router.post("/api/filters/save")
async def save_filter(
    user_id: str,
    filter_name: str,
    filter_config: dict,
    is_public: bool = False
):
    """
    Save a filter preset.
    """
    pass

@router.get("/api/filters/saved")
async def get_saved_filters(user_id: str):
    """
    Get all saved filters for user.
    """
    pass

@router.delete("/api/filters/{filter_id}")
async def delete_filter(filter_id: int, user_id: str):
    """
    Delete a saved filter.
    """
    pass
```

---

### 🎨 Frontend Implementation

**File:** `api/frontend/advanced-filters.html` (new component)

```html
<div class="advanced-filters-panel" id="advancedFilters">
    <div class="filter-header">
        <h3>סינון מתקדם</h3>
        <button onclick="toggleFilters()">✕</button>
    </div>
    
    <div class="filter-builder">
        <!-- Filter 1: Status -->
        <div class="filter-group">
            <label>סטטוס:</label>
            <select multiple id="statusFilter" class="multi-select">
                <option value="1">בקליטה</option>
                <option value="2">בטיפול</option>
                <option value="3">הושלם</option>
                <!-- ... more options ... -->
            </select>
        </div>
        
        <!-- Filter 2: Type -->
        <div class="filter-group">
            <label>סוג:</label>
            <select multiple id="typeFilter" class="multi-select">
                <option value="1">תכנון</option>
                <option value="4">בדיקה</option>
                <!-- ... more options ... -->
            </select>
        </div>
        
        <!-- Filter 3: Person -->
        <div class="filter-group">
            <label>אחראי:</label>
            <input type="text" id="personFilter" placeholder="שם אחראי...">
        </div>
        
        <!-- Filter 4: Date Range -->
        <div class="filter-group">
            <label>תאריך:</label>
            <input type="date" id="dateStart" placeholder="מתאריך">
            <input type="date" id="dateEnd" placeholder="עד תאריך">
        </div>
        
        <!-- Filter 5: Project -->
        <div class="filter-group">
            <label>פרויקט:</label>
            <input type="text" id="projectFilter" placeholder="שם פרויקט...">
        </div>
    </div>
    
    <div class="filter-actions">
        <button onclick="applyFilters()">החל סינון</button>
        <button onclick="clearFilters()">נקה הכל</button>
        <button onclick="saveFilterPreset()">שמור כמצב שמור</button>
    </div>
    
    <!-- Saved Filters -->
    <div class="saved-filters">
        <h4>מצבים שמורים:</h4>
        <div id="savedFiltersList"></div>
    </div>
    
    <!-- Quick Filters -->
    <div class="quick-filters">
        <h4>סינונים מהירים:</h4>
        <button class="quick-filter-btn" onclick="applyQuickFilter('my_requests')">
            הבקשות שלי
        </button>
        <button class="quick-filter-btn" onclick="applyQuickFilter('urgent')">
            דחופות
        </button>
        <button class="quick-filter-btn" onclick="applyQuickFilter('recent')">
            אחרונות (30 יום)
        </button>
    </div>
</div>

<!-- Active Filters Display -->
<div class="active-filters" id="activeFilters">
    <span class="filter-chip">
        סטטוס: 1, 2, 3
        <button onclick="removeFilter('status')">×</button>
    </span>
    <span class="filter-chip">
        סוג: 4
        <button onclick="removeFilter('type')">×</button>
    </span>
    <!-- ... more chips ... -->
</div>
```

**JavaScript Functions:**

```javascript
let currentFilters = {
    status: [],
    type: [],
    person: null,
    dateStart: null,
    dateEnd: null,
    project: null
};

function applyFilters() {
    // Collect filter values
    currentFilters.status = Array.from(document.getElementById('statusFilter').selectedOptions)
        .map(opt => opt.value);
    currentFilters.type = Array.from(document.getElementById('typeFilter').selectedOptions)
        .map(opt => opt.value);
    currentFilters.person = document.getElementById('personFilter').value || null;
    currentFilters.dateStart = document.getElementById('dateStart').value || null;
    currentFilters.dateEnd = document.getElementById('dateEnd').value || null;
    currentFilters.project = document.getElementById('projectFilter').value || null;
    
    // Update active filters display
    updateActiveFiltersDisplay();
    
    // Perform search with filters
    performAdvancedSearch();
}

function performAdvancedSearch() {
    const filterConfig = {
        filters: [],
        logic: "AND"
    };
    
    // Build filter config
    if (currentFilters.status.length > 0) {
        filterConfig.filters.push({
            field: "requeststatusid",
            operator: "in",
            values: currentFilters.status
        });
    }
    
    if (currentFilters.type.length > 0) {
        filterConfig.filters.push({
            field: "requesttypeid",
            operator: "in",
            values: currentFilters.type
        });
    }
    
    if (currentFilters.person) {
        filterConfig.filters.push({
            field: "updatedby",
            operator: "contains",
            value: currentFilters.person
        });
    }
    
    if (currentFilters.dateStart || currentFilters.dateEnd) {
        filterConfig.filters.push({
            field: "requeststatusdate",
            operator: "date_range",
            start: currentFilters.dateStart,
            end: currentFilters.dateEnd
        });
    }
    
    if (currentFilters.project) {
        filterConfig.filters.push({
            field: "projectname",
            operator: "contains",
            value: currentFilters.project
        });
    }
    
    // Call API
    fetch('/api/search/advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filters: filterConfig,
            top_k: 20,
            include_details: true
        })
    })
    .then(response => response.json())
    .then(data => {
        displayResults(data);
    });
}

function updateActiveFiltersDisplay() {
    const container = document.getElementById('activeFilters');
    container.innerHTML = '';
    
    if (currentFilters.status.length > 0) {
        const chip = createFilterChip('status', `סטטוס: ${currentFilters.status.join(', ')}`);
        container.appendChild(chip);
    }
    
    if (currentFilters.type.length > 0) {
        const chip = createFilterChip('type', `סוג: ${currentFilters.type.join(', ')}`);
        container.appendChild(chip);
    }
    
    if (currentFilters.person) {
        const chip = createFilterChip('person', `אחראי: ${currentFilters.person}`);
        container.appendChild(chip);
    }
    
    // ... more filters ...
}

function createFilterChip(filterType, label) {
    const chip = document.createElement('span');
    chip.className = 'filter-chip';
    chip.innerHTML = `
        ${label}
        <button onclick="removeFilter('${filterType}')">×</button>
    `;
    return chip;
}

function removeFilter(filterType) {
    currentFilters[filterType] = filterType.includes('date') ? null : [];
    updateActiveFiltersDisplay();
    applyFilters();
}

function applyQuickFilter(filterType) {
    // Reset all filters
    clearFilters();
    
    switch(filterType) {
        case 'my_requests':
            // Get current user and filter
            currentFilters.person = getCurrentUser();
            break;
        case 'urgent':
            const today = new Date();
            const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
            currentFilters.dateStart = today.toISOString().split('T')[0];
            currentFilters.dateEnd = nextWeek.toISOString().split('T')[0];
            break;
        case 'recent':
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            currentFilters.dateStart = thirtyDaysAgo.toISOString().split('T')[0];
            currentFilters.dateEnd = new Date().toISOString().split('T')[0];
            break;
    }
    
    updateActiveFiltersDisplay();
    applyFilters();
}

function saveFilterPreset() {
    const filterName = prompt('שם למצב שמור:');
    if (!filterName) return;
    
    const filterConfig = {
        filters: buildFilterConfig(),
        logic: "AND"
    };
    
    fetch('/api/filters/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: getUserId(),
            filter_name: filterName,
            filter_config: filterConfig,
            is_public: false
        })
    })
    .then(() => {
        loadSavedFilters();
        alert('המצב נשמר בהצלחה!');
    });
}
```

---

### 🛠️ Backend Implementation

**Update `api/services.py`:**

```python
def advanced_search(self, filter_config: dict, top_k: int = 20) -> tuple:
    """
    Perform search with advanced filters.
    
    Args:
        filter_config: {
            'filters': [
                {'field': 'requeststatusid', 'operator': 'in', 'values': ['1', '2']},
                {'field': 'updatedby', 'operator': 'contains', 'value': 'אור גלילי'}
            ],
            'logic': 'AND'  # or 'OR'
        }
    """
    if not self.conn:
        self.connect_db()
    
    # Build WHERE clause from filters
    where_clauses = []
    params = []
    param_index = 1
    
    for filter_item in filter_config.get('filters', []):
        field = filter_item['field']
        operator = filter_item['operator']
        
        if operator == 'in':
            values = filter_item['values']
            placeholders = ','.join([f'%s' for _ in values])
            where_clauses.append(f"r.{field}::TEXT IN ({placeholders})")
            params.extend(values)
        
        elif operator == 'equals':
            where_clauses.append(f"r.{field}::TEXT = %s")
            params.append(filter_item['value'])
        
        elif operator == 'contains':
            where_clauses.append(f"r.{field} ILIKE %s")
            params.append(f"%{filter_item['value']}%")
        
        elif operator == 'date_range':
            if filter_item.get('start'):
                where_clauses.append(f"r.{field} >= %s::DATE")
                params.append(filter_item['start'])
            if filter_item.get('end'):
                where_clauses.append(f"r.{field} <= %s::DATE")
                params.append(filter_item['end'])
    
    # Combine with logic (AND/OR)
    logic = filter_config.get('logic', 'AND')
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    # Execute search
    search_sql = f"""
        SELECT 
            r.requestid,
            r.projectname,
            r.updatedby,
            r.createdby,
            r.requesttypeid,
            r.requeststatusid,
            r.requeststatusdate
        FROM requests r
        {where_sql}
        ORDER BY r.requeststatusdate DESC
        LIMIT %s
    """
    params.append(top_k)
    
    self.cursor.execute(search_sql, tuple(params))
    results = self.cursor.fetchall()
    
    # Convert to dict format
    requests = []
    for row in results:
        requests.append({
            'requestid': row[0],
            'projectname': row[1],
            'updatedby': row[2],
            'createdby': row[3],
            'requesttypeid': row[4],
            'requeststatusid': row[5],
            'requeststatusdate': row[6].isoformat() if row[6] else None
        })
    
    # Get total count
    count_sql = f"SELECT COUNT(*) FROM requests r {where_sql}"
    self.cursor.execute(count_sql, tuple(params[:-1]))  # Remove LIMIT param
    total_count = self.cursor.fetchone()[0]
    
    return requests, total_count
```

---

### 📝 Implementation Steps

**Step 1: Database Setup (15 minutes)**
```sql
-- Create saved_filters table
```

**Step 2: Backend API (3-4 hours)**
1. Add advanced search endpoint
2. Implement filter parsing logic
3. Add saved filters endpoints
4. Test with various filter combinations

**Step 3: Frontend UI (4-5 hours)**
1. Create filter panel HTML
2. Add filter builder JavaScript
3. Add active filters display
4. Add quick filters
5. Style with CSS

**Step 4: Integration (2 hours)**
1. Integrate with existing search
2. Add filter persistence
3. Test end-to-end

**Total Time: ~10-12 hours**

---

## 3. Dashboard & Analytics

### 📖 Feature Description

**What it does:**
- **Statistics Dashboard:** Visual overview of request metrics
- **Charts & Graphs:** Pie charts, bar charts, line graphs
- **Real-time Updates:** Live statistics
- **Customizable Widgets:** Users can arrange dashboard
- **Export Reports:** Download statistics as PDF/Excel

**User Benefits:**
- ✅ Quick overview of system status
- ✅ Identify trends and patterns
- ✅ Make data-driven decisions
- ✅ Share insights with team

**Use Cases:**
- Manager wants to see: "How many requests per person this month?"
- Admin wants to see: "What are the most common request types?"
- Worker wants to see: "What's my completion rate?"
- Team wants to see: "What's our average response time?"

---

### 🎯 User Stories

1. **As a manager**, I want to see request statistics by person so I can track workload
2. **As an admin**, I want to see request trends over time so I can plan resources
3. **As a user**, I want to see my personal statistics so I can track my performance
4. **As a team**, I want to see team statistics so we can improve together

---

### 🗄️ Database Schema

**Optional: Pre-computed statistics table (for performance)**

```sql
CREATE TABLE request_statistics_cache (
    id SERIAL PRIMARY KEY,
    stat_type VARCHAR(50) NOT NULL,  -- 'by_status', 'by_type', 'by_person', etc.
    stat_key VARCHAR(200) NOT NULL,  -- The value (status ID, person name, etc.)
    stat_value INTEGER NOT NULL,  -- The count
    period_start DATE,
    period_end DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_type, stat_key, period_start, period_end)
);

CREATE INDEX idx_statistics_cache_type ON request_statistics_cache(stat_type, period_start);
```

---

### 🔌 API Endpoints

**File:** `api/routes/analytics.py` (new file)

```python
@router.get("/api/analytics/overview")
async def get_overview_stats():
    """
    Get overview statistics:
    - Total requests
    - Requests by status
    - Requests by type
    - Recent activity
    """
    pass

@router.get("/api/analytics/by-status")
async def get_stats_by_status():
    """
    Get request counts grouped by status.
    Returns: [{'status_id': '1', 'status_name': 'בקליטה', 'count': 150}, ...]
    """
    pass

@router.get("/api/analytics/by-type")
async def get_stats_by_type():
    """
    Get request counts grouped by type.
    """
    pass

@router.get("/api/analytics/by-person")
async def get_stats_by_person(limit: int = 10):
    """
    Get request counts grouped by person (top N).
    """
    pass

@router.get("/api/analytics/trends")
async def get_trends(
    period: str = "month",  # 'day', 'week', 'month', 'year'
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get request trends over time.
    Returns time series data for charts.
    """
    pass

@router.get("/api/analytics/personal/{user_id}")
async def get_personal_stats(user_id: str):
    """
    Get personal statistics for a user.
    """
    pass
```

---

### 🛠️ Service Layer Implementation

**Add to `api/services.py`:**

```python
class AnalyticsService:
    """Service for analytics and statistics."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect_db(self):
        """Connect to database."""
        if self.conn:
            return
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        self.conn = psycopg2.connect(
            host=host, port=int(port), database=database,
            user=user, password=password
        )
        self.cursor = self.conn.cursor()
    
    def get_overview_stats(self) -> dict:
        """Get overview statistics."""
        if not self.conn:
            self.connect_db()
        
        stats = {}
        
        # Total requests
        self.cursor.execute("SELECT COUNT(*) FROM requests")
        stats['total_requests'] = self.cursor.fetchone()[0]
        
        # Requests by status
        self.cursor.execute("""
            SELECT requeststatusid, COUNT(*) as count
            FROM requests
            GROUP BY requeststatusid
            ORDER BY count DESC
        """)
        stats['by_status'] = [
            {'status_id': row[0], 'count': row[1]}
            for row in self.cursor.fetchall()
        ]
        
        # Requests by type
        self.cursor.execute("""
            SELECT requesttypeid, COUNT(*) as count
            FROM requests
            GROUP BY requesttypeid
            ORDER BY count DESC
        """)
        stats['by_type'] = [
            {'type_id': row[0], 'count': row[1]}
            for row in self.cursor.fetchall()
        ]
        
        # Recent activity (last 7 days)
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM requests
            WHERE requeststatusdate >= CURRENT_DATE - INTERVAL '7 days'
        """)
        stats['recent_activity'] = self.cursor.fetchone()[0]
        
        return stats
    
    def get_stats_by_person(self, limit: int = 10) -> List[dict]:
        """Get top N people by request count."""
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute("""
            SELECT updatedby, COUNT(*) as count
            FROM requests
            WHERE updatedby IS NOT NULL AND updatedby != ''
            GROUP BY updatedby
            ORDER BY count DESC
            LIMIT %s
        """, (limit,))
        
        return [
            {'person': row[0], 'count': row[1]}
            for row in self.cursor.fetchall()
        ]
    
    def get_trends(self, period: str = 'month', days: int = 30) -> List[dict]:
        """Get request trends over time."""
        if not self.conn:
            self.connect_db()
        
        # Determine date grouping based on period
        if period == 'day':
            date_format = "DATE(requeststatusdate)"
            group_by = "DATE(requeststatusdate)"
        elif period == 'week':
            date_format = "DATE_TRUNC('week', requeststatusdate)"
            group_by = "DATE_TRUNC('week', requeststatusdate)"
        elif period == 'month':
            date_format = "DATE_TRUNC('month', requeststatusdate)"
            group_by = "DATE_TRUNC('month', requeststatusdate)"
        else:
            date_format = "DATE_TRUNC('year', requeststatusdate)"
            group_by = "DATE_TRUNC('year', requeststatusdate)"
        
        self.cursor.execute(f"""
            SELECT 
                {date_format} as period,
                COUNT(*) as count
            FROM requests
            WHERE requeststatusdate >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY {group_by}
            ORDER BY period
        """)
        
        return [
            {'period': row[0].isoformat() if row[0] else None, 'count': row[1]}
            for row in self.cursor.fetchall()
        ]
    
    def get_personal_stats(self, person_name: str) -> dict:
        """Get personal statistics for a person."""
        if not self.conn:
            self.connect_db()
        
        stats = {}
        
        # Total requests
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM requests
            WHERE updatedby ILIKE %s OR createdby ILIKE %s
        """, (f'%{person_name}%', f'%{person_name}%'))
        stats['total_requests'] = self.cursor.fetchone()[0]
        
        # By status
        self.cursor.execute("""
            SELECT requeststatusid, COUNT(*) as count
            FROM requests
            WHERE updatedby ILIKE %s OR createdby ILIKE %s
            GROUP BY requeststatusid
        """, (f'%{person_name}%', f'%{person_name}%'))
        stats['by_status'] = [
            {'status_id': row[0], 'count': row[1]}
            for row in self.cursor.fetchall()
        ]
        
        # Recent activity
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM requests
            WHERE (updatedby ILIKE %s OR createdby ILIKE %s)
            AND requeststatusdate >= CURRENT_DATE - INTERVAL '30 days'
        """, (f'%{person_name}%', f'%{person_name}%'))
        stats['recent_activity'] = self.cursor.fetchone()[0]
        
        return stats
```

---

### 🎨 Frontend Implementation

**File:** `api/frontend/dashboard.html` (new page)

```html
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="dashboard.css">
</head>
<body>
    <div class="dashboard-container">
        <header>
            <h1>📊 לוח בקרה - סטטיסטיקות</h1>
        </header>
        
        <!-- Overview Cards -->
        <div class="overview-cards">
            <div class="stat-card">
                <h3>סה"כ בקשות</h3>
                <div class="stat-value" id="totalRequests">-</div>
            </div>
            <div class="stat-card">
                <h3>פעילות אחרונה (7 ימים)</h3>
                <div class="stat-value" id="recentActivity">-</div>
            </div>
            <div class="stat-card">
                <h3>בקשות פתוחות</h3>
                <div class="stat-value" id="openRequests">-</div>
            </div>
        </div>
        
        <!-- Charts Row 1 -->
        <div class="charts-row">
            <div class="chart-container">
                <h3>בקשות לפי סטטוס</h3>
                <canvas id="statusChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>בקשות לפי סוג</h3>
                <canvas id="typeChart"></canvas>
            </div>
        </div>
        
        <!-- Charts Row 2 -->
        <div class="charts-row">
            <div class="chart-container">
                <h3>טופ 10 אחראים</h3>
                <canvas id="personChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>טרנדים (30 יום אחרונים)</h3>
                <canvas id="trendsChart"></canvas>
            </div>
        </div>
        
        <!-- Personal Stats (if user logged in) -->
        <div class="personal-stats" id="personalStats" style="display: none;">
            <h2>הסטטיסטיקות שלי</h2>
            <div class="personal-cards">
                <!-- Personal stats cards -->
            </div>
        </div>
    </div>
    
    <script src="dashboard.js"></script>
</body>
</html>
```

**JavaScript:**

```javascript
// Dashboard.js
class Dashboard {
    constructor() {
        this.charts = {};
    }
    
    async loadDashboard() {
        await Promise.all([
            this.loadOverview(),
            this.loadStatusChart(),
            this.loadTypeChart(),
            this.loadPersonChart(),
            this.loadTrendsChart()
        ]);
    }
    
    async loadOverview() {
        const response = await fetch('/api/analytics/overview');
        const data = await response.json();
        
        document.getElementById('totalRequests').textContent = data.total_requests;
        document.getElementById('recentActivity').textContent = data.recent_activity;
        
        // Calculate open requests (status != completed)
        const openCount = data.by_status
            .filter(s => s.status_id !== '10')  // Assuming 10 is completed
            .reduce((sum, s) => sum + s.count, 0);
        document.getElementById('openRequests').textContent = openCount;
    }
    
    async loadStatusChart() {
        const response = await fetch('/api/analytics/by-status');
        const data = await response.json();
        
        const ctx = document.getElementById('statusChart').getContext('2d');
        this.charts.status = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(d => `סטטוס ${d.status_id}`),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    async loadTypeChart() {
        const response = await fetch('/api/analytics/by-type');
        const data = await response.json();
        
        const ctx = document.getElementById('typeChart').getContext('2d');
        this.charts.type = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => `סוג ${d.type_id}`),
                datasets: [{
                    label: 'מספר בקשות',
                    data: data.map(d => d.count),
                    backgroundColor: '#36A2EB'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    async loadPersonChart() {
        const response = await fetch('/api/analytics/by-person?limit=10');
        const data = await response.json();
        
        const ctx = document.getElementById('personChart').getContext('2d');
        this.charts.person = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: data.map(d => d.person),
                datasets: [{
                    label: 'מספר בקשות',
                    data: data.map(d => d.count),
                    backgroundColor: '#FFCE56'
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    async loadTrendsChart() {
        const response = await fetch('/api/analytics/trends?period=day&days=30');
        const data = await response.json();
        
        const ctx = document.getElementById('trendsChart').getContext('2d');
        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.period),
                datasets: [{
                    label: 'מספר בקשות',
                    data: data.map(d => d.count),
                    borderColor: '#4BC0C0',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.loadDashboard();
    
    // Auto-refresh every 5 minutes
    setInterval(() => {
        dashboard.loadDashboard();
    }, 5 * 60 * 1000);
});
```

---

### 📝 Implementation Steps

**Step 1: Database Setup (Optional - 30 minutes)**
```sql
-- Create statistics cache table if needed
-- Or use direct queries (simpler for start)
```

**Step 2: Backend API (4-5 hours)**
1. Create `api/routes/analytics.py`
2. Add `AnalyticsService` to `api/services.py`
3. Implement all statistics queries
4. Test endpoints

**Step 3: Frontend (5-6 hours)**
1. Create dashboard HTML
2. Add Chart.js library
3. Implement JavaScript for charts
4. Style with CSS
5. Add auto-refresh

**Step 4: Integration (2 hours)**
1. Add dashboard link to main page
2. Test all charts
3. Optimize queries if slow

**Total Time: ~12-14 hours**

---

## 🎯 Summary

### Query History & Favorites
- **Time:** 6-8 hours
- **Complexity:** Low-Medium
- **Impact:** High (saves user time)

### Advanced Filters UI
- **Time:** 10-12 hours
- **Complexity:** Medium
- **Impact:** High (improves usability)

### Dashboard & Analytics
- **Time:** 12-14 hours
- **Complexity:** Medium
- **Impact:** High (provides insights)

**Total for all three: ~28-34 hours (1 week of focused work)**

---

## 🚀 Next Steps

1. **Start with Query History** - Easiest, high impact
2. **Then Advanced Filters** - Builds on search functionality
3. **Finally Dashboard** - Requires stable data structure

Each can be implemented independently and tested separately!

