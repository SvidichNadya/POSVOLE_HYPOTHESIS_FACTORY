import { apiGet, apiPost, extractUrls, shortenUrl, showSourcesModal } from './utils.js';

let currentFilter = 'all';
let currentQuery = '';

export function renderKnowledgeBase(documents) {
    const grid = document.getElementById('kb-resources-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const typeIcons = {
        paper: 'fa-file-invoice text-blue-500 bg-blue-50',
        patent: 'fa-certificate text-amber-500 bg-amber-50',
        report: 'fa-flask text-emerald-500 bg-emerald-50',
        dataset: 'fa-database text-purple-500 bg-purple-50'
    };
    const typeNames = {
        paper: 'Статья',
        patent: 'Патент',
        report: 'Отчет',
        dataset: 'Датасет'
    };
    documents.forEach(doc => {
        const card = document.createElement('div');
        card.className = "bg-white border-thin rounded-xl p-5 shadow-sm space-y-3 flex flex-col justify-between hover:border-brand/40 hover:shadow-md transition-all";
        let statusBadge = '';
        if (doc.status) {
            const statusColors = {
                pending: 'bg-gray-100 text-gray-600',
                processing: 'bg-yellow-100 text-yellow-700',
                completed: 'bg-green-100 text-green-700',
                failed: 'bg-red-100 text-red-700'
            };
            const statusLabels = {
                pending: 'В очереди',
                processing: 'Обработка...',
                completed: 'Готово',
                failed: 'Ошибка'
            };
            statusBadge = `<span class="text-[9px] ${statusColors[doc.status] || 'bg-gray-100'} px-1.5 py-0.5 rounded">${statusLabels[doc.status] || doc.status}</span>`;
        }

        // Извлекаем ссылки из метаданных и аннотации
        const metaUrls = extractUrls(doc.meta || '');
        const abstractUrls = extractUrls(doc.abstract || '');
        const allUrls = [...metaUrls, ...abstractUrls];
        const uniqueUrls = [...new Set(allUrls)];

        card.innerHTML = `
            <div class="space-y-2">
                <div class="flex justify-between items-center">
                    <span class="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[9px] font-bold uppercase ${doc.doc_type === 'patent' ? 'bg-amber-50 text-amber-700' : 'bg-brand-light text-brand'}">
                        <i class="fa-solid ${typeIcons[doc.doc_type]?.split(' ')[0] || 'fa-file'}"></i>
                        <span>${typeNames[doc.doc_type] || doc.doc_type}</span>
                    </span>
                    <span class="text-[10px] text-slate-400">${statusBadge}</span>
                </div>
                <h4 class="text-sm font-bold text-slate-900 leading-snug line-clamp-2">${doc.title}</h4>
                <p class="text-[10px] text-slate-400 italic">${doc.meta || ''}</p>
                <p class="text-xs text-slate-500 line-clamp-3">${doc.abstract}</p>
                ${doc.progress ? `<div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden"><div class="bg-brand h-full" style="width: ${doc.progress}%"></div></div>` : ''}
            </div>
            <div class="space-y-3 pt-3 border-t border-slate-100">
                <div class="flex flex-wrap gap-1">
                    ${(doc.tags || []).map(t => `<span class="text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.2 rounded">${t}</span>`).join('')}
                </div>
                <div class="flex items-center justify-between">
                    <div class="flex space-x-2 pt-1 text-xs">
                        <button onclick="viewKBSource(${doc.id})" class="flex-1 py-1.5 border border-slate-200 hover:border-brand hover:text-brand rounded-lg font-semibold text-slate-600 transition-all text-center">Читать</button>
                        <button onclick="downloadKBFile()" class="px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg text-slate-500 transition-all"><i class="fa-solid fa-download"></i></button>
                    </div>
                    ${uniqueUrls.length > 0 ? `<button onclick="showSourcesModal(${JSON.stringify(uniqueUrls.map(u => ({url: u, label: shortenUrl(u)})))}, 'Источники документа')" class="text-[10px] text-brand hover:underline">${uniqueUrls.length} ссылок</button>` : ''}
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

export function filterKBCategory(cat) {
    currentFilter = cat;
    document.querySelectorAll('.kb-cat-btn').forEach(btn => {
        btn.className = "kb-cat-btn px-3 py-1.5 bg-slate-50 text-slate-600 border border-slate-200 rounded-lg text-xs font-semibold transition-all hover:bg-slate-100";
    });
    const active = document.getElementById(`kb-cat-${cat}`);
    if (active) {
        active.className = "kb-cat-btn px-3 py-1.5 bg-brand text-white rounded-lg text-xs font-semibold transition-all";
    }
    reloadKnowledge();
}

export function handleKBSearch() {
    currentQuery = document.getElementById('kb-search-input')?.value || '';
    reloadKnowledge();
}

function reloadKnowledge() {
    const query = currentQuery;
    const type = currentFilter;
    apiGet(`knowledge/?type=${type}&q=${encodeURIComponent(query)}`)
        .then(data => renderKnowledgeBase(data))
        .catch(err => console.error('Knowledge reload error:', err));
}

window.handleKBPublish = function() {
    console.log('handleKBPublish вызвана');
    
    const sourceType = document.getElementById('upload-source-type')?.value;
    const docType = document.getElementById('upload-type')?.value;
    const title = document.getElementById('upload-title')?.value || '';
    const meta = document.getElementById('upload-meta')?.value || '';
    
    const formData = new FormData();
    formData.append('doc_type', docType || 'paper');
    formData.append('title', title);
    formData.append('meta', meta);
    formData.append('source_type', sourceType || 'web');
    
    const freshOnly = document.getElementById('kb-filter-fresh')?.checked || false;
    const verifiedOnly = document.getElementById('kb-filter-verified')?.checked || false;
    const exactMatch = document.getElementById('kb-filter-exact')?.checked || false;
    formData.append('fresh_only', freshOnly ? 'true' : 'false');
    formData.append('verified_only', verifiedOnly ? 'true' : 'false');
    formData.append('exact_match', exactMatch ? 'true' : 'false');
    
    if (sourceType === 'file') {
        const fileInput = document.getElementById('upload-file');
        if (!fileInput || !fileInput.files[0]) {
            window.showToast('Выберите файл', 'error');
            return;
        }
        formData.append('file', fileInput.files[0]);
    } else {
        const path = document.getElementById('upload-path')?.value;
        if (!path || path.trim() === '') {
            window.showToast('Введите тему для поиска', 'error');
            return;
        }
        formData.append('external_path', path.trim());
    }
    
    const token = window.API_TOKEN || '';
    fetch('/api/knowledge/create/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`
        },
        body: formData
    })
    .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    })
    .then(data => {
        window.closeModal('modal-upload-kb');
        window.showToast(data.message || 'Индексация запущена', 'info');
        reloadKnowledge();
    })
    .catch(err => {
        console.error('Upload error:', err);
        window.showToast('Ошибка: ' + err.message, 'error');
    });
};

window.viewKBSource = function(id) {
    window.showToast('Просмотр документа #' + id, 'info');
};

window.downloadKBFile = function() {
    window.showToast('Загрузка файла...', 'info');
};