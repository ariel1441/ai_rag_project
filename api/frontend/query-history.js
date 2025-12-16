/**
 * Query History Feature - Frontend Module
 * 
 * This is an optional feature that can be easily enabled/disabled.
 * To disable: Set ENABLE_QUERY_HISTORY=false or remove this script from index.html
 */

class QueryHistory {
    constructor() {
        this.enabled = false; // Will be checked from API
        this.userId = this.getUserId();
        this.recentQueries = [];
        this.favoriteQueries = [];
    }
    
    getUserId() {
        // Simple implementation - use session ID or email
        let userId = localStorage.getItem('queryHistory_userId');
        if (!userId) {
            userId = 'user_' + Date.now();
            localStorage.setItem('queryHistory_userId', userId);
        }
        return userId;
    }
    
    async checkEnabled() {
        // Check if feature is enabled by trying to fetch recent queries
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/query-history/recent?user_id=${this.userId}&limit=1`
            );
            this.enabled = response.status !== 503;
            return this.enabled;
        } catch (error) {
            this.enabled = false;
            return false;
        }
    }
    
    async saveQuery(queryText, queryType, intent, resultCount, executionTime) {
        if (!this.enabled) return;
        
        try {
            // Build request body - only include non-null/undefined values
            const requestBody = {
                user_id: this.userId,
                query_text: queryText,
                query_type: queryType
            };
            
            // Add optional fields only if they have values
            if (intent !== null && intent !== undefined && intent !== '') {
                requestBody.intent = intent;
            }
            if (resultCount !== null && resultCount !== undefined) {
                requestBody.result_count = resultCount;
            }
            if (executionTime !== null && executionTime !== undefined) {
                requestBody.execution_time_ms = Math.round(executionTime); // Ensure integer
            }
            
            const response = await fetch(`${API_BASE_URL}/api/query-history/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            if (response.ok) {
                // Reload recent queries
                await this.loadRecentQueries();
            } else {
                // Log error for debugging
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                console.debug('Query history save failed:', response.status, errorData);
            }
        } catch (error) {
            console.debug('Query history save failed (non-critical):', error);
        }
    }
    
    async loadRecentQueries(limit = 10) {
        if (!this.enabled) return;
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/query-history/recent?user_id=${this.userId}&limit=${limit}`
            );
            if (response.ok) {
                this.recentQueries = await response.json();
                this.renderRecentQueries();
            }
        } catch (error) {
            console.debug('Failed to load recent queries:', error);
        }
    }
    
    async loadFavoriteQueries() {
        if (!this.enabled) return;
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/query-history/favorites?user_id=${this.userId}`
            );
            if (response.ok) {
                this.favoriteQueries = await response.json();
                this.renderFavoriteQueries();
            }
        } catch (error) {
            console.debug('Failed to load favorites:', error);
        }
    }
    
    async getSuggestions(prefix) {
        if (!this.enabled || prefix.length < 2) return [];
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/query-history/suggestions?user_id=${this.userId}&prefix=${encodeURIComponent(prefix)}&limit=5`
            );
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.debug('Failed to get suggestions:', error);
        }
        return [];
    }
    
    renderRecentQueries() {
        const container = document.getElementById('recentQueries');
        if (!container) return;
        
        container.innerHTML = '<h3>חיפושים אחרונים</h3>';
        
        if (this.recentQueries.length === 0) {
            container.innerHTML += '<p class="empty-state">אין חיפושים אחרונים</p>';
            return;
        }
        
        const list = document.createElement('ul');
        list.className = 'query-list';
        this.recentQueries.forEach(query => {
            const li = document.createElement('li');
            li.className = 'query-item';
            li.innerHTML = `
                <span class="query-text" onclick="queryHistory.runQuery('${this.escapeHtml(query.query_text)}', '${query.query_type}')">
                    ${this.escapeHtml(query.query_text)}
                </span>
                <span class="query-meta">${query.result_count || 0} תוצאות</span>
                <button onclick="queryHistory.toggleFavorite(${query.id})" class="favorite-btn ${query.is_favorite ? 'active' : ''}" title="${query.is_favorite ? 'הסר ממועדפים' : 'הוסף למועדפים'}">
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
            container.innerHTML += '<p class="empty-state">אין חיפושים מועדפים</p>';
            return;
        }
        
        const list = document.createElement('ul');
        list.className = 'query-list';
        this.favoriteQueries.forEach(query => {
            const li = document.createElement('li');
            li.className = 'query-item';
            li.innerHTML = `
                <span class="query-text" onclick="queryHistory.runQuery('${this.escapeHtml(query.query_text)}', '${query.query_type}')">
                    ${this.escapeHtml(query.query_text)}
                </span>
                <button onclick="queryHistory.toggleFavorite(${query.id})" class="favorite-btn active" title="הסר ממועדפים">★</button>
            `;
            list.appendChild(li);
        });
        container.appendChild(list);
    }
    
    async toggleFavorite(queryId) {
        if (!this.enabled) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/query-history/favorite/${queryId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId })
            });
            
            if (response.ok) {
                await this.loadRecentQueries();
                await this.loadFavoriteQueries();
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }
    
    runQuery(queryText, queryType) {
        // Set input value and trigger search
        document.getElementById('queryInput').value = queryText;
        const radio = document.querySelector(`input[value="${queryType}"]`);
        if (radio) {
            radio.checked = true;
        }
        performSearch();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async initAutocomplete() {
        if (!this.enabled) return;
        
        const queryInput = document.getElementById('queryInput');
        if (!queryInput) return;
        
        let suggestionsList = null;
        let debounceTimer = null;
        let selectedIndex = -1;
        let currentSuggestions = [];
        
        // Ensure input group has relative positioning
        const inputGroup = queryInput.parentElement;
        if (inputGroup) {
            inputGroup.style.position = 'relative';
        }
        
        const showSuggestions = (suggestions) => {
            // Remove existing suggestions
            if (suggestionsList) {
                suggestionsList.remove();
                suggestionsList = null;
            }
            
            if (suggestions.length === 0) return;
            
            currentSuggestions = suggestions;
            selectedIndex = -1;
            
            // Create suggestions dropdown
            suggestionsList = document.createElement('ul');
            suggestionsList.className = 'suggestions-list';
            suggestionsList.id = 'autocomplete-suggestions';
            
            suggestions.forEach((s, index) => {
                const li = document.createElement('li');
                li.style.padding = '8px';
                li.style.cursor = 'pointer';
                li.style.listStyle = 'none';
                li.textContent = s;
                li.dataset.index = index;
                li.onmouseover = () => {
                    selectedIndex = index;
                    updateHighlight();
                };
                li.onmouseout = () => {
                    selectedIndex = -1;
                    updateHighlight();
                };
                li.onclick = () => {
                    selectSuggestion(s);
                };
                suggestionsList.appendChild(li);
            });
            
            // Position below input (not covering it)
            const inputRect = queryInput.getBoundingClientRect();
            suggestionsList.style.position = 'absolute';
            suggestionsList.style.top = (queryInput.offsetHeight + 2) + 'px';
            suggestionsList.style.left = '0px';
            suggestionsList.style.width = queryInput.offsetWidth + 'px';
            suggestionsList.style.zIndex = '1000';
            suggestionsList.style.backgroundColor = 'white';
            suggestionsList.style.border = '1px solid #ccc';
            suggestionsList.style.borderRadius = '4px';
            suggestionsList.style.maxHeight = '200px';
            suggestionsList.style.overflowY = 'auto';
            suggestionsList.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            
            inputGroup.appendChild(suggestionsList);
        };
        
        const updateHighlight = () => {
            if (!suggestionsList) return;
            const items = suggestionsList.querySelectorAll('li');
            items.forEach((li, index) => {
                if (index === selectedIndex) {
                    li.style.backgroundColor = '#e3f2fd';
                    li.style.fontWeight = 'bold';
                } else {
                    li.style.backgroundColor = 'white';
                    li.style.fontWeight = 'normal';
                }
            });
        };
        
        const selectSuggestion = (suggestion) => {
            queryInput.value = suggestion;
            if (suggestionsList) {
                suggestionsList.remove();
                suggestionsList = null;
            }
            selectedIndex = -1;
            currentSuggestions = [];
        };
        
        queryInput.addEventListener('input', async (e) => {
            const prefix = e.target.value;
            
            // Remove existing suggestions while typing
            if (suggestionsList) {
                suggestionsList.remove();
                suggestionsList = null;
            }
            selectedIndex = -1;
            currentSuggestions = [];
            
            // Clear previous debounce timer
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }
            
            if (prefix.length < 2) return;
            
            // Debounce: wait 500ms after user stops typing (increased from 300ms)
            debounceTimer = setTimeout(async () => {
                const suggestions = await this.getSuggestions(prefix);
                showSuggestions(suggestions);
            }, 500); // 500ms debounce delay
        });
        
        // Keyboard navigation
        queryInput.addEventListener('keydown', (e) => {
            if (!suggestionsList || currentSuggestions.length === 0) return;
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
                updateHighlight();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateHighlight();
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                selectSuggestion(currentSuggestions[selectedIndex]);
            } else if (e.key === 'Escape') {
                if (suggestionsList) {
                    suggestionsList.remove();
                    suggestionsList = null;
                }
                selectedIndex = -1;
                currentSuggestions = [];
            }
        });
        
        // Remove suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (suggestionsList && !queryInput.contains(e.target) && !suggestionsList.contains(e.target)) {
                suggestionsList.remove();
                suggestionsList = null;
                selectedIndex = -1;
                currentSuggestions = [];
            }
        });
    }
}

// Initialize query history (if enabled)
const queryHistory = new QueryHistory();

// Check if enabled and initialize
document.addEventListener('DOMContentLoaded', async () => {
    const enabled = await queryHistory.checkEnabled();
    if (enabled) {
        await queryHistory.loadRecentQueries();
        await queryHistory.loadFavoriteQueries();
        await queryHistory.initAutocomplete();
    }
});

