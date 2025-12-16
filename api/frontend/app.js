const API_BASE_URL = 'http://localhost:8000';

// Handle Enter key in input
document.getElementById('queryInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Update hint when option changes
document.querySelectorAll('input[name="searchType"]').forEach(radio => {
    radio.addEventListener('change', function() {
        updateOptionHint();
    });
});

function updateOptionHint() {
    const selected = document.querySelector('input[name="searchType"]:checked').value;
    const hintElement = document.getElementById('optionHint');
    
    const hints = {
        'search': 'חיפוש מהיר - מציג רשימת בקשות ללא תשובה טקסטואלית (~3-5 שניות)',
        'rag-no-llm': 'RAG מהיר - חיפוש משופר ללא תשובה טקסטואלית (~3-5 שניות)',
        'rag-full': 'RAG מלא - חיפוש + תשובה טקסטואלית. איטי בפעם הראשונה (~2-5 דקות), מהיר אחר כך (~5-15 שניות)'
    };
    
    hintElement.textContent = hints[selected] || '';
}

async function performSearch() {
    const query = document.getElementById('queryInput').value.trim();
    if (!query) {
        showStatus('אנא הזן שאילתה', 'error');
        return;
    }

    const searchType = document.querySelector('input[name="searchType"]:checked').value;
    
    // Clear previous results
    document.getElementById('results').classList.add('hidden');
    document.getElementById('answer').classList.add('hidden');
    
    // Show loading with appropriate message
    let loadingMsg = 'מחפש...';
    if (searchType === 'rag-full') {
        loadingMsg = 'מחפש ומייצר תשובה... (זה יכול לקחת זמן בפעם הראשונה)';
    }
    showStatus(loadingMsg, 'loading');
    
    try {
        if (searchType === 'search') {
            await performSearchOnly(query);
        } else if (searchType === 'rag-no-llm') {
            await performRAG(query, false);
        } else {
            await performRAG(query, true);
        }
    } catch (error) {
        showStatus(`שגיאה: ${error.message}`, 'error');
        console.error('Error:', error);
    }
}

async function performSearchOnly(query) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: 20,
                include_details: true
            })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({detail: `HTTP ${response.status}: ${response.statusText}`}));
            throw new Error(error.detail || 'Search failed');
        }
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError') || error.name === 'TypeError') {
            throw new Error('Cannot connect to API server. Make sure the server is running on http://localhost:8000');
        }
        throw error;
    }

    const data = await response.json();
    
    const displayedCount = data.results.length;
    const totalCount = data.total_found;
    let statusMsg = `נמצאו ${totalCount} בקשות`;
    if (displayedCount < totalCount) {
        statusMsg += ` (מציג ${displayedCount} הראשונות)`;
    }
    statusMsg += ` (${(data.search_time_ms / 1000).toFixed(2)} שניות)`;
    showStatus(statusMsg, 'success');
    displayResults(data.results, data.intent, data.entities, totalCount);
    
    // Optional: Save query to history (non-breaking)
    if (typeof queryHistory !== 'undefined' && queryHistory.enabled) {
        queryHistory.saveQuery(
            query,
            'search',
            data.intent,
            totalCount,
            data.search_time_ms
        ).catch(err => console.debug('Query history save failed:', err));
    }
}

async function performRAG(query, useLLM) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}/api/rag/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: 20,
                use_llm: useLLM
            })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({detail: `HTTP ${response.status}: ${response.statusText}`}));
            const errorMsg = error.detail || 'RAG query failed';
            // Show user-friendly error message
            showStatus(`שגיאה: ${errorMsg}`, 'error');
            throw new Error(errorMsg);
        }
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError') || error.name === 'TypeError') {
            const msg = 'Cannot connect to API server. Make sure the server is running on http://localhost:8000';
            showStatus(`שגיאה: ${msg}`, 'error');
            throw new Error(msg);
        }
        throw error;
    }

    const data = await response.json();
    
    const timeText = useLLM 
        ? `${(data.response_time_ms / 1000).toFixed(2)} שניות${data.model_loaded ? ' (מודל נטען)' : ' (טוען מודל...)'}`
        : `${(data.response_time_ms / 1000).toFixed(2)} שניות`;
    
    showStatus(`נמצאו ${data.total_retrieved} תוצאות (${timeText})`, 'success');
    
    if (data.answer) {
        displayAnswer(data.answer);
    }
    
    displayResults(data.requests || [], data.intent, data.entities, data.total_retrieved);
    
    // Optional: Save query to history (non-breaking)
    if (typeof queryHistory !== 'undefined' && queryHistory.enabled) {
        const queryType = useLLM ? 'rag-full' : 'rag-no-llm';
        queryHistory.saveQuery(
            query,
            queryType,
            data.intent,
            data.total_retrieved,
            data.response_time_ms
        ).catch(err => console.debug('Query history save failed:', err));
    }
}

function displayResults(results, intent, entities, totalCount = null) {
    const resultsDiv = document.getElementById('results');
    const contentDiv = document.getElementById('resultsContent');
    
    if (!results || results.length === 0) {
        contentDiv.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">לא נמצאו תוצאות</p>';
        resultsDiv.classList.remove('hidden');
        return;
    }

    let html = '';
    
    // Show total count if provided
    if (totalCount !== null && totalCount > results.length) {
        html += `<div style="background: #fff3cd; padding: 10px; border-radius: 8px; margin-bottom: 15px; text-align: center;">
            <strong>סה"כ נמצאו ${totalCount} בקשות</strong> (מציג ${results.length} הראשונות)
        </div>`;
    }
    
    // Show intent and entities
    if (intent || entities) {
        html += '<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">';
        if (intent) {
            html += `<strong>כוונה:</strong> ${intent} `;
        }
        if (entities && Object.keys(entities).length > 0) {
            html += `<strong>ישויות:</strong> ${JSON.stringify(entities, null, 2)}`;
        }
        html += '</div>';
    }

    results.forEach((req, index) => {
        html += `
            <div class="request-card" onclick="toggleDetails(${index})">
                <div class="request-header">
                    <span class="request-id">בקשה #${req.requestid || 'N/A'}</span>
                    ${req.similarity ? `<span class="request-similarity">דמיון: ${(req.similarity * 100).toFixed(1)}%</span>` : ''}
                </div>
                <div class="request-preview">
                    ${req.projectname ? `<strong>פרויקט:</strong> ${req.projectname}<br>` : ''}
                    ${req.updatedby ? `<strong>עודכן על ידי:</strong> ${req.updatedby}<br>` : ''}
                    ${req.createdby ? `<strong>נוצר על ידי:</strong> ${req.createdby}<br>` : ''}
                </div>
                <div class="request-details">
                    ${req.projectdesc ? `<div class="detail-row"><span class="detail-label">תיאור פרויקט:</span><span class="detail-value">${req.projectdesc}</span></div>` : ''}
                    ${req.areadesc ? `<div class="detail-row"><span class="detail-label">תיאור אזור:</span><span class="detail-value">${req.areadesc}</span></div>` : ''}
                    ${req.remarks ? `<div class="detail-row"><span class="detail-label">הערות:</span><span class="detail-value">${req.remarks}</span></div>` : ''}
                    ${req.responsibleemployeename ? `<div class="detail-row"><span class="detail-label">אחראי:</span><span class="detail-value">${req.responsibleemployeename}</span></div>` : ''}
                    ${req.contactfirstname || req.contactlastname ? `<div class="detail-row"><span class="detail-label">איש קשר:</span><span class="detail-value">${req.contactfirstname || ''} ${req.contactlastname || ''}</span></div>` : ''}
                    ${req.contactemail ? `<div class="detail-row"><span class="detail-label">אימייל:</span><span class="detail-value">${req.contactemail}</span></div>` : ''}
                    ${req.requesttypeid ? `<div class="detail-row"><span class="detail-label">סוג בקשה:</span><span class="detail-value">${req.requesttypeid}</span></div>` : ''}
                    ${req.requeststatusid ? `<div class="detail-row"><span class="detail-label">סטטוס:</span><span class="detail-value">${req.requeststatusid}</span></div>` : ''}
                </div>
            </div>
        `;
    });

    contentDiv.innerHTML = html;
    resultsDiv.classList.remove('hidden');
}

function displayAnswer(answer) {
    const answerDiv = document.getElementById('answer');
    const contentDiv = document.getElementById('answerContent');
    
    contentDiv.textContent = answer;
    answerDiv.classList.remove('hidden');
}

function toggleDetails(index) {
    const cards = document.querySelectorAll('.request-card');
    const card = cards[index];
    card.classList.toggle('expanded');
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.classList.remove('hidden');
}

