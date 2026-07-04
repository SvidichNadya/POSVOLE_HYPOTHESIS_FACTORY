import { apiGet, apiPost, apiPatch, extractUrls, shortenUrl, showSourcesModal } from './utils.js';
import { renderDashboard } from './dashboard.js';
import { renderObjectsList, selectObject } from './objects.js';
import { renderHypothesesList, selectHypothesis, generateHypothesis } from './hypotheses.js';
import { initGraph } from './graph.js';
import { renderKnowledgeBase, filterKBCategory } from './knowledge.js';

window.filterKBCategory = filterKBCategory;

window.switchTab = function(tabId) {
    window.activeTab = tabId;
    document.querySelectorAll('.tab-section').forEach(sec => sec.classList.add('hidden'));
    const target = document.getElementById(`tab-${tabId}`);
    if (target) target.classList.remove('hidden');
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.className = "nav-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-600 hover:bg-slate-50 hover:text-slate-900";
    });
    const activeBtn = document.getElementById(`nav-${tabId}`);
    if (activeBtn) {
        activeBtn.className = "nav-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-[#135BEC] bg-brand-light font-semibold";
    }
    if (tabId === 'dashboard') loadDashboard();
    else if (tabId === 'projects') { loadProjects(); fillProjectSelects(); }
    else if (tabId === 'objects') { loadObjects(); }
    else if (tabId === 'hypotheses') { loadHypotheses(); window.updateFormObjects(); }
    else if (tabId === 'graph') {
        setTimeout(() => { initGraph(); }, 100);
    }
    else if (tabId === 'knowledge') loadKnowledge();
};

window.showToast = function(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `p-3 rounded-lg border shadow-md bg-white flex items-center pointer-events-auto max-w-sm text-xs font-medium z-50`;
    toast.innerHTML = `<span class="text-brand mr-2">●</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
};

window.openModal = function(id) { document.getElementById(id)?.classList.remove('hidden'); };
window.closeModal = function(id) { document.getElementById(id)?.classList.add('hidden'); };
window.quickStartAnalysis = function() { window.switchTab('hypotheses'); };

let currentProjectId = null;

// ---------- ПРОЕКТЫ ----------
function fillProjectSelects() {
    const objSelect = document.getElementById('proj-object');
    const hypoSelect = document.getElementById('proj-hypo');
    if (!objSelect || !hypoSelect) return;

    apiGet('objects/').then(objects => {
        objSelect.innerHTML = '<option value="">-- Не выбрано --</option>';
        objects.forEach(obj => {
            const opt = document.createElement('option');
            opt.value = obj.id;
            opt.textContent = obj.name;
            objSelect.appendChild(opt);
        });
    }).catch(() => {});

    apiGet('hypotheses/').then(hypotheses => {
        hypoSelect.innerHTML = '<option value="">-- Не выбрано --</option>';
        hypotheses.forEach(h => {
            const opt = document.createElement('option');
            opt.value = h.id;
            opt.textContent = h.title;
            hypoSelect.appendChild(opt);
        });
    }).catch(() => {});
}

window.loadProjects = function() {
    apiGet('projects/').then(data => {
        const container = document.getElementById('projects-list-col');
        container.innerHTML = '';
        data.forEach(p => {
            const item = document.createElement('div');
            item.className = `p-4 bg-white border border-slate-200 rounded-xl cursor-pointer hover:border-brand/50 transition-all`;
            item.onclick = () => window.selectProject(p.id);
            item.innerHTML = `
                <div class="flex justify-between items-start">
                    <h4 class="text-sm font-bold text-slate-900">${p.name}</h4>
                    <span class="text-[9px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">${p.status}</span>
                </div>
                <div class="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
                    <div class="bg-brand h-full" style="width: ${p.progress || 0}%"></div>
                </div>
                <div class="flex justify-between mt-1 text-[10px] text-slate-400">
                    <span>ROI: ${p.business_roi || 0}x</span>
                    <span>Успех: ${Math.round(p.success_probability * 100)}%</span>
                </div>
            `;
            container.appendChild(item);
        });
    }).catch(err => console.warn('Projects load error:', err));
};

window.toggleChecklistItem = function(projectId, itemIdx, isChecked) {
    apiGet(`projects/${projectId}/`).then(proj => {
        if (!proj.checklist) proj.checklist = [];
        if (proj.checklist[itemIdx]) {
            proj.checklist[itemIdx].done = isChecked;
        }
        apiPatch(`projects/${projectId}/checklist/`, { checklist: proj.checklist })
            .then(res => {
                window.selectProject(projectId);
                window.loadProjects();
                window.showToast('Чек-лист обновлён', 'info');
            });
    }).catch(err => window.showToast('Ошибка обновления чек-листа', 'error'));
};

window.selectProject = function(id) {
    apiGet(`projects/${id}/`).then(data => {
        const pane = document.getElementById('project-workspace');
        let checklistHTML = (data.checklist || []).map((task, idx) => `
            <div class="flex items-center space-x-2 text-xs bg-white p-2 border border-slate-100 rounded">
                <input type="checkbox" ${task.done ? 'checked' : ''} onchange="toggleChecklistItem(${data.id}, ${idx}, this.checked)" class="text-brand rounded">
                <span class="${task.done ? 'line-through text-slate-400' : 'text-slate-700'}">${task.task}</span>
            </div>
        `).join('');

        // Обработка аналогов: извлекаем ссылки
        const analogsText = data.analogs || '';
        const analogUrls = extractUrls(analogsText);
        let analogsDisplay = analogsText;
        if (analogUrls.length > 0) {
            // Заменяем длинные ссылки на короткие названия
            let shortAnalogs = analogsText;
            analogUrls.forEach((url, idx) => {
                const short = shortenUrl(url);
                shortAnalogs = shortAnalogs.replace(url, short);
            });
            analogsDisplay = shortAnalogs;
        }

        pane.innerHTML = `
            <div class="flex flex-wrap justify-between items-start border-b pb-4 gap-2">
                <div>
                    <h3 class="text-xl font-bold">${data.name}</h3>
                    <p class="text-xs text-slate-500 mt-1">${data.description || ''}</p>
                </div>
                <div class="flex items-center space-x-2 text-xs">
                    <span class="bg-brand-light text-brand px-2 py-1 rounded font-semibold">ROI: ${data.business_roi}x</span>
                    <span class="bg-emerald-50 text-emerald-700 px-2 py-1 rounded font-semibold">Успех: ${Math.round(data.success_probability * 100)}%</span>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-xs">
                <div class="bg-red-50 p-3 rounded border border-red-100 text-red-900">
                    <strong>Риски:</strong><br>${data.risks || '—'}
                </div>
                <div class="bg-emerald-50 p-3 rounded border border-emerald-100 text-emerald-900">
                    <strong>Как избежать:</strong><br>${data.risk_mitigation || '—'}
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2 text-xs">
                <div class="bg-slate-50 p-2 rounded"><span class="text-slate-400 block">Оптимистичный</span><span class="font-medium">${data.optimistic_scenario || '—'}</span></div>
                <div class="bg-slate-50 p-2 rounded"><span class="text-slate-400 block">Оптимальный</span><span class="font-medium">${data.optimal_scenario || '—'}</span></div>
                <div class="bg-slate-50 p-2 rounded"><span class="text-slate-400 block">Пессимистичный</span><span class="font-medium">${data.pessimistic_scenario || '—'}</span></div>
            </div>
            <div class="mt-4 p-4 bg-slate-50 rounded border">
                <div class="flex justify-between items-center">
                    <h4 class="text-xs font-bold uppercase text-slate-500">Чек-лист проекта (авто-статус)</h4>
                    <span class="text-[10px] text-slate-400">Прогресс: ${data.progress}%</span>
                </div>
                <div class="space-y-2 mt-2">${checklistHTML || '<span class="text-xs text-slate-400">Чек-лист пока не сгенерирован</span>'}</div>
            </div>
            <div class="mt-4 grid grid-cols-2 gap-4 text-xs bg-slate-50 p-3 rounded border">
                <div><span class="text-slate-400 block">Стоимость НИОКР</span><span class="font-bold">$${data.business_cost}</span></div>
                <div><span class="text-slate-400 block">Окупаемость</span><span class="font-bold">${data.business_payback} мес.</span></div>
                <div class="col-span-2">
                    <div class="flex justify-between items-center">
                        <span class="text-slate-400 block">Аналоги:</span>
                        <span class="font-medium text-slate-700">${analogsDisplay || '—'}</span>
                        ${analogUrls.length > 0 ? `<button onclick="showSourcesModal(${JSON.stringify(analogUrls.map(u => ({url: u, label: shortenUrl(u)})))}, 'Аналоги проекта')" class="text-[10px] text-brand hover:underline ml-2">(${analogUrls.length} ссылок)</button>` : ''}
                    </div>
                </div>
                <div class="col-span-2"><span class="text-slate-400 block">Требуемые ресурсы</span><span class="font-medium">${data.resources_needed || '—'}</span></div>
            </div>
        `;
    }).catch(err => console.warn('Project detail error:', err));
};

window.submitNewProject = function(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Анализ данных...';
    btn.disabled = true;

    const data = {
        name: document.getElementById('proj-name').value,
        description: document.getElementById('proj-desc').value,
        available_resources: document.getElementById('proj-res-avail').value,
        object_id: document.getElementById('proj-object').value || null,
        hypothesis_id: document.getElementById('proj-hypo').value || null
    };

    if (!data.name) {
        window.showToast('Введите название проекта', 'error');
        btn.innerHTML = 'Создать проект';
        btn.disabled = false;
        return;
    }

    fetch('/api/projects/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${window.API_TOKEN}`
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.error) {
            window.showToast('Ошибка: ' + result.error, 'error');
        } else {
            window.closeModal('modal-add-project');
            document.getElementById('project-form').reset();
            window.showToast('Проект создан!', 'success');
            window.loadProjects();
        }
    })
    .catch(err => {
        window.showToast('Ошибка соединения', 'error');
        console.error(err);
    })
    .finally(() => {
        btn.innerHTML = 'Создать проект';
        btn.disabled = false;
    });
};

// ---------- ОБНОВЛЕНИЕ ВЫПАДАЮЩИХ СПИСКОВ ДЛЯ ГИПОТЕЗ ----------
window.updateFormObjects = function() {
    const select = document.getElementById('form-object');
    if (!select) return;
    apiGet('objects/').then(objects => {
        select.innerHTML = '<option value="">-- Без привязки к объекту --</option>';
        objects.forEach(obj => {
            const option = document.createElement('option');
            option.value = obj.id;
            option.textContent = obj.name;
            select.appendChild(option);
        });
        select.onchange = function() { window.updateFormKPIs(); };
        window.updateFormKPIs();
    }).catch(err => console.warn('Не удалось загрузить объекты:', err));
};

window.updateFormKPIs = function() {
    const objectId = document.getElementById('form-object').value;
    const kpiSelect = document.getElementById('form-kpi-target');
    const customContainer = document.getElementById('custom-kpi-container');

    if (!objectId) {
        kpiSelect.innerHTML = `
            <option value="Ресурс службы">Ресурс службы</option>
            <option value="Прочность">Прочность</option>
            <option value="Стоимость">Стоимость</option>
            <option value="Плотность энергии">Плотность энергии</option>
            <option value="custom">Свой KPI</option>
        `;
        kpiSelect.onchange = (e) => {
            if (e.target.value === 'custom') customContainer.classList.remove('hidden');
            else customContainer.classList.add('hidden');
        };
        customContainer.classList.add('hidden');
        return;
    }

    apiGet(`objects/${objectId}/`).then(data => {
        kpiSelect.innerHTML = '';
        (data.metrics || []).forEach(m => {
            const option = document.createElement('option');
            option.value = m.name;
            option.textContent = m.name;
            kpiSelect.appendChild(option);
        });
        kpiSelect.innerHTML += '<option value="custom">Свой пользовательский KPI...</option>';
        kpiSelect.onchange = (e) => {
            if (e.target.value === 'custom') customContainer.classList.remove('hidden');
            else customContainer.classList.add('hidden');
        };
        customContainer.classList.add('hidden');
    });
};

// ---------- ЗАГРУЗКА ДАННЫХ ДЛЯ ВКЛАДОК ----------
function loadDashboard() { apiGet('dashboard/').then(renderDashboard); }
function loadObjects() { apiGet('objects/').then(data => { renderObjectsList(data); window.updateFormObjects(); }); }
export function loadHypotheses() { apiGet('hypotheses/').then(renderHypothesesList); }
window.loadKnowledge = function() { apiGet('knowledge/').then(renderKnowledgeBase); };

// Создание гипотезы из рекомендации (глобальная функция)
window.createHypothesisFromRecommendation = function() {
    const rec = window.lastRecommendation;
    if (!rec) {
        window.showToast('Рекомендация ещё не загружена', 'error');
        return;
    }
    
    const btn = document.getElementById('create-from-rec-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i>Создание...';
    }
    
    const targetName = rec.target_object || '';
    let objectId = null;
    
    apiGet('objects/').then(objects => {
        const found = objects.find(o => o.name.toLowerCase() === targetName.toLowerCase());
        if (found) objectId = found.id;
        
        const payload = {
            object_id: objectId,
            kpi_target: rec.kpi || 'Ключевой показатель',
            kpi_val: rec.expected_roi ? `ROI ${rec.expected_roi}x` : 'Улучшение',
            approach: rec.description || rec.title || '',
            budget: 150000,
            duration: 6,
            team: { scientists: 2, engineers: 2, equipment: 'mid' }
        };
        
        window.showToast('Генерация гипотезы...', 'info');
        return apiPost('hypotheses/generate/', payload);
    })
    .then(hypo => {
        window.showToast('Гипотеза успешно создана!', 'success');
        window.switchTab('hypotheses');
        setTimeout(() => {
            import('./hypotheses.js').then(module => {
                module.loadHypotheses();
                setTimeout(() => {
                    window.selectHypothesis(hypo.id);
                }, 300);
            });
        }, 200);
    })
    .catch(err => {
        console.error('Error creating hypothesis:', err);
        window.showToast('Ошибка создания гипотезы: ' + err.message, 'error');
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-lightbulb mr-1"></i>Создать гипотезу из рекомендации';
        }
    });
};

document.addEventListener('DOMContentLoaded', () => {
    window.switchTab('dashboard');
    window.updateFormObjects();
    fillProjectSelects();

    const form = document.getElementById('hypothesis-wizard-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            let kpi = document.getElementById('form-kpi-target').value;
            if (kpi === 'custom' || !kpi) kpi = document.getElementById('form-custom-kpi').value;

            const objectId = document.getElementById('form-object').value;
            const payload = {
                object_id: objectId || null,
                kpi_target: kpi,
                kpi_val: document.getElementById('form-kpi-val').value || '',
                budget: document.getElementById('form-budget').value || null,
                duration: document.getElementById('form-duration').value || null,
                approach: document.getElementById('form-approach').value || 'Без описания',
                team: {
                    scientists: parseInt(document.getElementById('form-sci-count').value) || 0,
                    engineers: parseInt(document.getElementById('form-eng-count').value) || 0,
                    equipment: document.getElementById('form-equipment').value || 'mid'
                }
            };
            window.showToast('Запуск расчётов...', 'info');
            apiPost('hypotheses/generate/', payload)
                .then(() => {
                    window.showToast('Гипотеза успешно сгенерирована!');
                    loadHypotheses();
                })
                .catch(err => window.showToast('Ошибка: ' + err.message, 'error'));
        });
    }
});

// Создание гипотезы из рекомендации объекта
window.createHypothesisFromObjectRecommendation = function(recText) {
    // Переключаемся на вкладку гипотез
    window.switchTab('hypotheses');
    
    // Ждём, пока форма появится в DOM
    let attempts = 0;
    const maxAttempts = 30; // 3 секунды максимум
    const waitForForm = setInterval(() => {
        attempts++;
        const approachField = document.getElementById('form-approach');
        if (approachField) {
            clearInterval(waitForForm);
            // Заполняем поле
            approachField.value = recText;
            // Показываем тост
            window.showToast('Рекомендация добавлена в форму. Нажмите "Рассчитать и сгенерировать"', 'info');
            // Находим кнопку отправки и подсвечиваем её
            const submitBtn = document.querySelector('#hypothesis-wizard-form button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('animate-pulse', 'ring-2', 'ring-brand', 'ring-offset-2');
                // Снимаем подсветку через 5 секунд
                setTimeout(() => {
                    submitBtn.classList.remove('animate-pulse', 'ring-2', 'ring-brand', 'ring-offset-2');
                }, 5000);
            }
        } else if (attempts >= maxAttempts) {
            clearInterval(waitForForm);
            window.showToast('Не удалось загрузить форму генерации. Попробуйте переключить вкладку вручную.', 'error');
        }
    }, 100);
    
    // Таймаут на случай, если форма не загрузится
    setTimeout(() => {
        clearInterval(waitForForm);
    }, 3000);
};

// Глобальные функции для использования в HTML
window.selectProject = selectProject;
window.loadProjects = loadProjects;
window.toggleChecklistItem = toggleChecklistItem;
window.submitNewProject = submitNewProject;