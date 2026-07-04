import { apiGet, apiPost, apiPatch, extractUrls, shortenUrl, showSourcesModal } from './utils.js';

let currentObjectId = null;

export function renderObjectsList(objects) {
    const container = document.getElementById('objects-list-col');
    if (!container) return;
    container.innerHTML = '';
    objects.forEach(obj => {
        const item = document.createElement('div');
        item.className = `p-4 bg-white border rounded-xl cursor-pointer transition-all space-y-2 ${obj.id === currentObjectId ? 'border-brand ring-1 ring-brand-light' : 'border-slate-200 hover:border-brand/50'}`;
        item.id = `obj-card-${obj.id}`;
        item.onclick = () => selectObject(obj.id);
        item.innerHTML = `
            <div class="flex justify-between items-start">
                <h4 class="text-sm font-bold text-slate-900">${obj.name}</h4>
                <span class="text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-bold">${obj.status || 'Новый'}</span>
            </div>
            <p class="text-xs text-slate-500 line-clamp-2">${obj.description || ''}</p>
        `;
        container.appendChild(item);
    });
}

export function selectObject(objectId) {
    currentObjectId = objectId;
    document.querySelectorAll('[id^="obj-card-"]').forEach(el => {
        el.className = "p-4 bg-white border border-slate-200 rounded-xl cursor-pointer transition-all hover:border-brand/50 space-y-2";
    });
    const activeCard = document.getElementById(`obj-card-${objectId}`);
    if (activeCard) {
        activeCard.className = "p-4 bg-white border border-brand ring-1 ring-brand-light rounded-xl cursor-pointer transition-all space-y-2";
    }
    apiGet(`objects/${objectId}/`)
        .then(data => renderObjectWorkspace(data))
        .catch(err => console.error('Error loading object details:', err));
}

window.editMetric = function(metricId, currentVal, targetVal) {
    const newVal = prompt("Текущее значение:", currentVal);
    const newTar = prompt("Целевое значение:", targetVal);
    if (newVal !== null && newTar !== null) {
        apiPatch(`objects/metrics/${metricId}/`, { current_value: newVal, target_value: newTar })
            .then(() => {
                window.showToast('KPI обновлён');
                selectObject(currentObjectId);
            })
            .catch(err => window.showToast('Ошибка обновления', 'error'));
    }
};

function safeString(val) {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'object') {
        if (val.value !== undefined) return String(val.value);
        if (val.current !== undefined) return String(val.current);
        try {
            return JSON.stringify(val);
        } catch {
            return '—';
        }
    }
    return String(val);
}

export function renderObjectWorkspace(data) {
    if (!data) return;
    const container = document.getElementById('object-workspace');
    if (!container) return;

    const name = data.name || 'Без названия';
    const description = data.description || '';
    const status = data.status || 'Новый';

    const metrics = data.metrics || [];
    let metricsHtml = '';
    if (metrics.length === 0) {
        metricsHtml = `<div class="col-span-full text-xs text-slate-400 text-center py-4">Нет показателей</div>`;
    } else {
        metricsHtml = metrics.map(m => `
            <div class="bg-slate-50 border border-slate-100 p-3 rounded-xl relative group">
                <span class="text-[10px] text-slate-400 font-semibold uppercase block">${safeString(m.name) || 'Без имени'}</span>
                <div class="flex items-baseline space-x-1.5 mt-1">
                    <span class="text-sm font-bold text-slate-800">${safeString(m.current)}</span>
                    <span class="text-[10px] text-slate-400 font-medium">/ цель ${safeString(m.target)}</span>
                </div>
                <button onclick="editMetric(${m.id}, '${safeString(m.current)}', '${safeString(m.target)}')" class="absolute top-2 right-2 text-slate-300 hover:text-brand hidden group-hover:block"><i class="fa-solid fa-pen text-[10px]"></i></button>
            </div>
        `).join('');
    }

    const bottlenecks = data.bottlenecks || [];
    const strengths = data.strengths || [];
    const bottlenecksHtml = bottlenecks.length ? bottlenecks.map(b => `<li class="text-xs text-red-900">${safeString(b.description)}</li>`).join('') : '<li class="text-xs text-red-400">Не указаны</li>';
    const strengthsHtml = strengths.length ? strengths.map(s => `<li class="text-xs text-emerald-950">${safeString(s.description)}</li>`).join('') : '<li class="text-xs text-emerald-400">Не указаны</li>';

    const sliders = data.sliders || [];
    let slidersHtml = '';
    if (sliders.length === 0) {
        slidersHtml = `<div class="col-span-full text-xs text-slate-400 text-center py-4">Нет параметров для моделирования</div>`;
    } else {
        slidersHtml = sliders.map(s => `
            <div class="space-y-1">
                <div class="flex justify-between text-xs">
                    <span class="text-slate-600">${safeString(s.name) || safeString(s.key)}</span>
                    <span class="text-brand font-medium" id="slider-val-${s.key}">${safeString(s.default) || 0}</span>
                </div>
                <input type="range" name="${s.key}" id="slider-${s.key}" 
                    min="${safeString(s.min) || 0}" max="${safeString(s.max) || 100}" step="${safeString(s.step) || 1}" value="${safeString(s.default) || 0}"
                    oninput="handleSliderChange(${data.id}, '${s.key}', this.value)"
                    class="w-full">
                <div class="flex justify-between text-[9px] text-slate-400">
                    <span>${safeString(s.min) || 0}</span>
                    <span>${safeString(s.max) || 100}</span>
                </div>
            </div>
        `).join('');
    }

    container.innerHTML = `
        <div class="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
                <h3 id="workspace-obj-name" class="text-lg font-bold text-slate-900">${safeString(name)}</h3>
                <p id="workspace-obj-desc" class="text-xs text-slate-500 mt-0.5">${safeString(description)}</p>
            </div>
            <span class="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded font-semibold" id="workspace-obj-status">${safeString(status)}</span>
        </div>

        <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Текущий цифровой профиль</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4" id="workspace-metrics-grid">
                ${metricsHtml}
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 bg-red-50 rounded-lg border border-red-100 space-y-2">
                <h4 class="text-xs font-bold text-red-700 uppercase tracking-wider flex items-center space-x-1.5"><i class="fa-solid fa-triangle-exclamation"></i><span>Узкие места</span></h4>
                <ul class="text-xs text-red-900 space-y-1.5" id="workspace-bottlenecks-list">
                    ${bottlenecksHtml}
                </ul>
            </div>
            <div class="p-4 bg-emerald-50 rounded-lg border border-emerald-100 space-y-2">
                <h4 class="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center space-x-1.5"><i class="fa-solid fa-shield-halved"></i><span>Сильные стороны</span></h4>
                <ul class="text-xs text-emerald-950 space-y-1.5" id="workspace-strengths-list">
                    ${strengthsHtml}
                </ul>
            </div>
        </div>

        <div class="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-4">
            <div class="flex justify-between items-center">
                <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center space-x-1.5"><i class="fa-solid fa-sliders text-brand"></i><span>What-If Моделирование</span></h4>
                <span class="text-[10px] bg-brand-light text-brand px-2 py-0.5 rounded font-bold">Предиктивный движок</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6" id="workspace-sliders-container">
                ${slidersHtml}
            </div>
            <div class="pt-4 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div class="bg-white p-2.5 rounded border border-slate-200"><span class="text-[10px] text-slate-400 font-semibold block">Ресурс</span><span class="text-sm font-bold text-slate-800 sim-kpi-value" id="sim-kpi-1">—</span></div>
                <div class="bg-white p-2.5 rounded border border-slate-200"><span class="text-[10px] text-slate-400 font-semibold block">Прочность</span><span class="text-sm font-bold text-slate-800 sim-kpi-value" id="sim-kpi-2">—</span></div>
                <div class="bg-white p-2.5 rounded border border-slate-200"><span class="text-[10px] text-slate-400 font-semibold block">Стоимость</span><span class="text-sm font-bold text-slate-800 sim-kpi-value" id="sim-kpi-3">—</span></div>
                <div class="bg-white p-2.5 rounded border border-slate-200"><span class="text-[10px] text-slate-400 font-semibold block">Плотность</span><span class="text-sm font-bold text-slate-800 sim-kpi-value" id="sim-kpi-4">—</span></div>
            </div>
        </div>

        <div class="p-4 bg-brand-light/30 border border-brand-light rounded-lg">
            <h4 class="text-[10px] font-bold uppercase text-brand mb-2"><i class="fa-solid fa-wand-magic-sparkles"></i> Стратегическая рекомендация</h4>
            <div id="workspace-ai-recommendation">
                <span class="text-xs text-slate-400">Анализ данных... <i class="fa-solid fa-spinner fa-spin"></i></span>
            </div>
        </div>

        <div class="space-y-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Привязанные гипотезы</h4>
            <div class="space-y-2" id="workspace-related-hypotheses">
                <span class="text-xs text-slate-400">Загрузка...</span>
            </div>
        </div>
    `;

    apiGet(`hypotheses/?object_id=${data.id}`).then(hypotheses => {
        const containerHyp = document.getElementById('workspace-related-hypotheses');
        if (!containerHyp) return;
        if (!hypotheses || hypotheses.length === 0) {
            containerHyp.innerHTML = `<span class="text-xs text-slate-400">Нет привязанных гипотез. Сгенерируйте новую.</span>`;
            return;
        }
        containerHyp.innerHTML = hypotheses.map(h => `
            <div onclick="window.switchTab('hypotheses'); window.selectHypothesis(${h.id});" class="flex justify-between items-center p-3 bg-slate-50 hover:bg-white border border-slate-100 hover:border-brand/30 rounded-lg cursor-pointer transition-all">
                <div class="space-y-0.5">
                    <span class="text-xs font-bold text-slate-800 block">${safeString(h.title)}</span>
                    <span class="text-[9px] text-slate-400">Новизна: ${safeString(h.novelty_score)}% | Вероятность: ${Math.round(safeString(h.feasibility_score) * 100)}%</span>
                </div>
                <span class="text-xs text-brand font-bold">ROI: ${safeString(h.roi)}x <i class="fa-solid fa-arrow-right ml-1"></i></span>
            </div>
        `).join('');
    }).catch(err => console.warn('Failed to load related hypotheses:', err));

    const recBox = document.getElementById('workspace-ai-recommendation');
    if (recBox) {
        apiGet(`objects/${data.id}/recommendation/`).then(res => {
            const recText = safeString(res.recommendation);
            const urls = extractUrls(recText);
            let recDisplay = recText;
            if (urls.length > 0) {
                urls.forEach((url) => {
                    const short = shortenUrl(url);
                    recDisplay = recDisplay.replace(url, short);
                });
            }
            recBox.innerHTML = `
                <p class="text-xs text-brand-dark italic border-l-2 border-brand pl-2">${recDisplay}</p>
                ${urls.length > 0 ? `<button onclick="showSourcesModal(${JSON.stringify(urls.map(u => ({url: u, label: shortenUrl(u)})))}, 'Источники рекомендации')" class="mt-2 text-[10px] text-brand underline hover:no-underline">Показать источники (${urls.length})</button>` : ''}
                <button onclick="window.createHypothesisFromObjectRecommendation('${recText.replace(/'/g, "\\'")}')" class="mt-2 text-[10px] bg-brand text-white px-2 py-1 rounded hover:bg-brand-dark transition-all">Создать гипотезу из рекомендации</button>
            `;
        }).catch(err => {
            recBox.innerHTML = '<span class="text-xs text-red-400">Не удалось загрузить рекомендацию</span>';
        });
    }

    window.currentObjectId = data.id;
    recalculateSimulation(data.id);
}

window.handleSliderChange = function(objectId, key, value) {
    const valDisplay = document.getElementById(`slider-val-${key}`);
    if (valDisplay) valDisplay.innerText = value;
    recalculateSimulation(objectId);
};

function recalculateSimulation(objectId) {
    const sliders = document.querySelectorAll('#workspace-sliders-container input[type="range"]');
    const sliderValues = {};
    sliders.forEach(input => {
        const key = input.name || input.id.replace('slider-', '');
        sliderValues[key] = parseFloat(input.value);
    });
    apiPost('simulate/', { object_id: objectId, sliders: sliderValues })
        .then(result => {
            const kpiElements = document.querySelectorAll('.sim-kpi-value');
            if (kpiElements.length >= 4) {
                kpiElements[0].innerText = safeString(result.kpi1);
                kpiElements[1].innerText = safeString(result.kpi2);
                kpiElements[2].innerText = safeString(result.kpi3);
                kpiElements[3].innerText = safeString(result.kpi4);
            }
        })
        .catch(err => console.error('Simulation error:', err));
}

window.handlePublishObject = function() {
    const name = document.getElementById('obj-new-name').value;
    const desc = document.getElementById('obj-new-desc').value;

    if (!name) {
        window.showToast('Введите название объекта', 'error');
        return;
    }

    const data = {
        name: name,
        description: desc,
        metrics: [
            {
                name: document.getElementById('obj-kpi-1-name').value,
                current_value: document.getElementById('obj-kpi-1-cur').value,
                target_value: document.getElementById('obj-kpi-1-tar').value,
                unit: document.getElementById('obj-kpi-1-unit')?.value || ''
            },
            {
                name: document.getElementById('obj-kpi-2-name').value,
                current_value: document.getElementById('obj-kpi-2-cur').value,
                target_value: document.getElementById('obj-kpi-2-tar').value,
                unit: document.getElementById('obj-kpi-2-unit')?.value || ''
            }
        ]
    };

    apiPost('objects/create/', data)
        .then(() => {
            window.closeModal('modal-add-object');
            window.showToast('Объект успешно создан', 'success');
            apiGet('objects/').then(objects => {
                renderObjectsList(objects);
                if (window.updateFormObjects) window.updateFormObjects();
            });
        })
        .catch(err => window.showToast('Ошибка: ' + err.message, 'error'));
};