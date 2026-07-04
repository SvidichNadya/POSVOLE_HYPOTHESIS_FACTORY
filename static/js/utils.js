// static/js/utils.js
const API_BASE = '/api/';

function getToken() {
    if (typeof window !== 'undefined' && window.API_TOKEN) {
        return window.API_TOKEN;
    }
    console.warn('API_TOKEN не определён');
    return '';
}

export function apiGet(url) {
    return fetch(API_BASE + url, {
        headers: { 'Authorization': `Token ${getToken()}` }
    }).then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    });
}

export function apiPost(url, data) {
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

/**
 * Извлечение всех URL из текста (включая DOI)
 */
export function extractUrls(text) {
    if (!text) return [];
    // Регулярка для URL и DOI
    const urlRegex = /(https?:\/\/[^\s]+|doi:\s*[^\s]+|10\.\d{4,9}\/[-._;()/:A-Z0-9]+)/gi;
    const matches = text.match(urlRegex) || [];
    // Очищаем от лишних символов
    return matches.map(u => u.trim().replace(/[.,;:!?)]$/, '')).filter(u => u.length > 5);
}

/**
 * Сокращение URL для отображения
 */
export function shortenUrl(url) {
    if (!url) return 'Источник';
    try {
        // Если это DOI
        if (url.startsWith('10.') || url.includes('doi.org')) {
            const doiMatch = url.match(/10\.\d{4,9}\/[-._;()/:A-Z0-9]+/i);
            if (doiMatch) return `DOI: ${doiMatch[0].slice(0, 20)}...`;
        }
        // Если это URL
        const parsed = new URL(url);
        let host = parsed.hostname.replace('www.', '');
        // Обрезаем длинные пути
        const path = parsed.pathname.length > 15 ? parsed.pathname.slice(0, 15) + '…' : parsed.pathname;
        return host + path;
    } catch {
        // Если не удалось распарсить, обрезаем
        return url.length > 30 ? url.slice(0, 30) + '…' : url;
    }
}

/**
 * Отображение модального окна со списком ссылок
 */
export function showSourcesModal(sources, title = 'Источники') {
    // Создаём или получаем существующее модальное окно
    let modal = document.getElementById('modal-sources');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-sources';
        modal.className = 'fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 hidden';
        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 border-thin space-y-4 max-h-[80vh] flex flex-col">
                <div class="flex justify-between items-center pb-2 border-b border-slate-100">
                    <h3 class="font-bold text-sm text-slate-900 uppercase tracking-wider" id="sources-modal-title">Источники</h3>
                    <button onclick="closeModal('modal-sources')" class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2" id="sources-list-container">
                    <!-- Список будет заполнен -->
                </div>
                <div class="pt-2 border-t border-slate-100 flex justify-end">
                    <button onclick="closeModal('modal-sources')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-semibold transition-all">Закрыть</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Заполняем список
    const container = document.getElementById('sources-list-container');
    const titleEl = document.getElementById('sources-modal-title');
    titleEl.textContent = title;

    if (!sources || sources.length === 0) {
        container.innerHTML = '<div class="text-xs text-slate-400 text-center py-8">Нет активных ссылок</div>';
    } else {
        container.innerHTML = sources.map((src, idx) => {
            const displayUrl = src.url || src;
            const label = src.label || `Источник ${idx + 1}`;
            return `
                <div class="flex items-start space-x-2 text-xs p-2 bg-slate-50 rounded border border-slate-100">
                    <span class="font-mono text-brand font-semibold shrink-0">${idx + 1}.</span>
                    <div class="flex-1 min-w-0">
                        <div class="font-medium text-slate-700">${label}</div>
                        <a href="${displayUrl}" target="_blank" rel="noopener noreferrer" class="text-brand hover:underline break-all">${displayUrl}</a>
                    </div>
                    <button onclick="navigator.clipboard.writeText('${displayUrl}')" class="text-slate-400 hover:text-brand transition-all shrink-0" title="Копировать ссылку">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
            `;
        }).join('');
    }

    // Показываем модалку
    modal.classList.remove('hidden');
}

// Добавляем функцию в глобальный объект для использования из HTML
window.showSourcesModal = showSourcesModal;
window.extractUrls = extractUrls;
window.shortenUrl = shortenUrl;