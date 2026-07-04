import { apiGet, apiPost, apiPatch, extractUrls, shortenUrl, showSourcesModal } from './utils.js';

let currentHypothesisId = null;

export function renderHypothesesList(hypotheses) {
    const container = document.getElementById('hypotheses-list-container');
    if (!container) return;
    container.innerHTML = '';
    hypotheses.forEach(h => {
        const item = document.createElement('div');
        item.className = `p-3 bg-slate-50 hover:bg-white border border-slate-100 hover:border-slate-200 rounded-lg cursor-pointer transition-all space-y-1 ${h.id === currentHypothesisId ? 'border-brand ring-1 ring-brand-light' : ''}`;
        item.id = `hypo-item-${h.id}`;
        item.onclick = () => selectHypothesis(h.id);
        const sos = Math.round(h.novelty_score * 0.3 + h.roi * 10);
        item.innerHTML = `
            <div class="flex justify-between items-start">
                <span class="text-xs font-bold text-slate-800 line-clamp-1">${h.title}</span>
                <span class="text-[9px] bg-brand-light text-brand px-1.5 py-0.2 rounded font-bold shrink-0 ml-2">SOS: ${sos}</span>
            </div>
            <div class="flex justify-between items-center text-[10px] text-slate-400">
                <span>Затраты: $${h.research_cost}</span>
                <span class="font-bold text-slate-600">ROI: ${h.roi}x</span>
            </div>
        `;
        container.appendChild(item);
    });
}

export function selectHypothesis(hypoId) {
    currentHypothesisId = hypoId;
    document.querySelectorAll('[id^="hypo-item-"]').forEach(el => {
        el.className = "p-3 bg-slate-50 hover:bg-white border border-slate-100 hover:border-slate-200 rounded-lg cursor-pointer transition-all space-y-1";
    });
    const active = document.getElementById(`hypo-item-${hypoId}`);
    if (active) {
        active.className = "p-3 bg-white border border-brand ring-1 ring-brand-light rounded-lg cursor-pointer transition-all space-y-1";
    }
    apiGet(`hypotheses/${hypoId}/`)
        .then(data => renderHypothesisDetail(data))
        .catch(err => console.error('Error loading hypothesis details:', err));
}

export function renderHypothesisDetail(h) {
    const pane = document.getElementById('hypo-workspace-pane');
    if (!pane) return;
    const sos = Math.round(h.novelty_score * 0.3 + h.roi * 10);
    const targetObj = h.object_name || 'Неизвестный объект';

    // Собираем все ссылки из доказательств
    const evidences = h.evidences || [];
    const allSources = [];
    evidences.forEach(ev => {
        const urls = extractUrls(ev.text + ' ' + ev.source);
        urls.forEach(url => {
            allSources.push({
                url: url,
                label: ev.source || 'Источник'
            });
        });
        // Если source сам по себе является ссылкой
        if (ev.source && !urls.includes(ev.source) && (ev.source.startsWith('http') || ev.source.startsWith('10.'))) {
            allSources.push({
                url: ev.source,
                label: ev.source
            });
        }
    });

    // Уникализируем ссылки
    const uniqueSources = [];
    const seen = new Set();
    allSources.forEach(s => {
        const key = s.url;
        if (!seen.has(key)) {
            seen.add(key);
            uniqueSources.push(s);
        }
    });

    pane.innerHTML = `
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center pb-4 border-b border-slate-100 gap-4">
            <div class="space-y-1">
                <span class="text-[9px] bg-brand-light text-brand px-2.5 py-1 rounded-full uppercase font-bold tracking-wider">Карточка гипотезы: ${h.id}</span>
                <h3 class="text-lg font-bold text-slate-900">${h.title}</h3>
                <p class="text-xs text-slate-500">Объект: <strong>${targetObj}</strong></p>
            </div>
            <div class="flex items-center space-x-2">
                <span class="text-xs text-slate-400 font-medium">Статус:</span>
                <select onchange="updateHypothesisStatus(${h.id}, this.value)" class="p-1 px-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold">
                    <option value="idea" ${h.status === 'idea' ? 'selected' : ''}>Идея</option>
                    <option value="validation" ${h.status === 'validation' ? 'selected' : ''}>Валидация</option>
                    <option value="experiment" ${h.status === 'experiment' ? 'selected' : ''}>НИОКР / Эксперимент</option>
                    <option value="completed" ${h.status === 'completed' ? 'selected' : ''}>Завершено</option>
                </select>
            </div>
        </div>
        <p class="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">${h.description}</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="p-4 border border-slate-200 rounded-xl space-y-4">
                <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5 border-b pb-2"><i class="fa-solid fa-graduation-cap text-brand"></i><span>Научные индикаторы</span></h4>
                <div class="grid grid-cols-2 gap-4">
                    <div class="text-center space-y-1 bg-slate-50 p-3 rounded-lg"><span class="text-[10px] text-slate-400 font-semibold uppercase block">Novelty Score</span><div class="text-xl font-extrabold text-brand">${h.novelty_score}%</div></div>
                    <div class="text-center space-y-1 bg-slate-50 p-3 rounded-lg"><span class="text-[10px] text-slate-400 font-semibold uppercase block">Feasibility Score</span><div class="text-xl font-extrabold text-emerald-600">${Math.round(h.feasibility_score * 100)}%</div></div>
                </div>
                <div class="space-y-2">
                    <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Цепочка доказательств (XAI)</span>
                    <div class="space-y-2 pl-2 border-l-2 border-brand/30">
                        ${evidences.map((ev, idx) => {
                            // Извлекаем ссылки из текста доказательства
                            const urls = extractUrls(ev.text + ' ' + ev.source);
                            const shortSource = urls.length > 0 ? shortenUrl(urls[0]) : (ev.source || 'Источник');
                            return `
                                <div class="text-xs space-y-0.5">
                                    <div class="text-slate-700 flex items-start space-x-1">
                                        <span class="text-brand font-bold">${idx+1}.</span>
                                        <span>${ev.text}</span>
                                    </div>
                                    ${urls.length > 0 ? `<span class="text-[9px] text-brand underline cursor-pointer" onclick="showSourcesModal([${urls.map(u => `'${u}'`).join(',')}], 'Источники доказательства #${idx+1}')">${shortSource}</span>` : `<span class="text-[9px] text-slate-400">${shortSource}</span>`}
                                </div>
                            `;
                        }).join('')}
                    </div>
                    ${uniqueSources.length > 0 ? `
                        <button onclick="showSourcesModal(${JSON.stringify(uniqueSources)}, 'Все источники гипотезы')" class="mt-2 text-[10px] bg-brand-light text-brand px-2 py-1 rounded hover:bg-brand/10 transition-all flex items-center space-x-1">
                            <i class="fa-solid fa-link"></i>
                            <span>Показать все источники (${uniqueSources.length})</span>
                        </button>
                    ` : ''}
                </div>
            </div>
            <div class="p-4 border border-slate-200 rounded-xl space-y-4">
                <h4 class="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5 border-b pb-2"><i class="fa-solid fa-sack-dollar text-brand"></i><span>Бизнес и финансовый анализ</span></h4>
                <div class="grid grid-cols-2 gap-4 text-center">
                    <div class="bg-slate-50 p-2 rounded"><span class="text-[9px] text-slate-400 font-medium block">Стоимость НИОКР</span><span class="text-sm font-bold text-slate-800">$${h.research_cost}</span></div>
                    <div class="bg-slate-50 p-2 rounded"><span class="text-[9px] text-slate-400 font-medium block">Эффект</span><span class="text-sm font-bold text-emerald-600">$${h.economic_benefit}/год</span></div>
                    <div class="bg-slate-50 p-2 rounded"><span class="text-[9px] text-slate-400 font-medium block">Окупаемость</span><span class="text-sm font-bold text-slate-800">${h.payback_months} мес.</span></div>
                    <div class="bg-slate-50 p-2 rounded"><span class="text-[9px] text-slate-400 font-medium block">Research ROI</span><span class="text-sm font-bold text-brand">${h.roi}x</span></div>
                </div>
                <div class="p-3 bg-brand-light/40 border border-brand-light/70 rounded-lg space-y-1">
                    <span class="text-[10px] font-bold text-brand uppercase block">Scientific Opportunity Score (SOS)</span>
                    <div class="text-[10px] text-slate-600 leading-normal font-mono">SOS = (0.3 × Novelty) + (0.7 × (P(success) × Benefit / Cost))</div>
                    <div class="flex justify-between items-center pt-1.5 text-xs"><span class="font-medium text-slate-700">Итоговый индекс SOS:</span><span class="font-extrabold text-brand text-sm">${sos} / 100</span></div>
                </div>
            </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="p-4 border border-slate-200 rounded-xl space-y-3">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Оценка сложности (1-10)</span>
                ${Object.entries(h.complexity_data || {}).map(([key, val]) => `
                    <div>
                        <div class="flex justify-between text-slate-500 mb-0.5 text-xs"><span>${key.charAt(0).toUpperCase() + key.slice(1)}</span><span class="font-bold text-slate-700">${val}/10</span></div>
                        <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden"><div class="bg-brand h-full" style="width: ${val * 10}%"></div></div>
                    </div>
                `).join('')}
            </div>
            <div class="p-4 border border-slate-200 rounded-xl space-y-3">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Дорожная карта</span>
                ${(h.roadmap_steps || []).map((step, idx) => `
                    <div class="flex justify-between items-center text-xs p-2 bg-slate-50 border border-slate-100 rounded">
                        <div class="flex items-center space-x-2"><span class="w-5 h-5 rounded-full bg-brand text-white flex items-center justify-center font-bold text-[10px]">${idx+1}</span><span class="font-medium text-slate-800">${step.name}</span></div>
                        <div class="text-[10px] text-slate-400 flex items-center space-x-3"><span>${step.duration}</span><span class="font-bold ${step.risk_level === 'Высокий' ? 'text-red-500' : step.risk_level === 'Средний' ? 'text-amber-500' : 'text-emerald-500'}">${step.risk_level}</span></div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

window.updateHypothesisStatus = function(hypoId, status) {
    apiPatch(`hypotheses/${hypoId}/status/`, { status })
        .then(() => {
            window.showToast('Статус обновлён', 'success');
            apiGet('hypotheses/').then(data => renderHypothesesList(data));
        })
        .catch(err => window.showToast('Ошибка обновления статуса', 'error'));
};

export function generateHypothesis(payload) {
    return apiPost('hypotheses/generate/', payload);
}