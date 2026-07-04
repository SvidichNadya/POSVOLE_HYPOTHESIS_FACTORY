// static/js/api.js
const API_BASE = '/api/';

function getToken() {
    if (typeof window !== 'undefined' && window.API_TOKEN) {
        return window.API_TOKEN;
    }
    console.warn('API_TOKEN не определён. Проверьте загрузку token.js');
    return '';
}

export function apiGet(url) {
    return fetch(API_BASE + url, {
        headers: {
            'Authorization': `Token ${getToken()}`
        }
    }).then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    });
}

export function apiPost(url, data) {
    // Убедимся, что object_id – число, если он есть
    if (data && typeof data.object_id !== 'undefined') {
        data.object_id = Number(data.object_id);
    }
    return fetch(API_BASE + url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${getToken()}`
        },
        body: JSON.stringify(data)
    }).then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    });
}

export function apiPatch(url, data) {
    return fetch(API_BASE + url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${getToken()}`
        },
        body: JSON.stringify(data)
    }).then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    });
}