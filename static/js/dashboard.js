import { apiGet } from './utils.js';

export function renderDashboard(data) {
    if (!data) return;
    
    document.getElementById('best-hypo-title').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Анализ данных...';
    apiGet('dashboard/recommendation/').then(rec => {
        window.lastRecommendation = rec;
        
        const btn = document.getElementById('create-from-rec-btn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-lightbulb mr-1"></i>Создать гипотезу из рекомендации';
        }
        
        document.getElementById('best-hypo-title').innerText = rec.title || 'Новая научная парадигма';
        document.getElementById('best-hypo-desc').innerText = rec.description || '';
        document.getElementById('best-hypo-object').innerText = rec.target_object || 'Глобальный поиск';
        document.getElementById('best-hypo-roi').innerText = rec.expected_roi ? rec.expected_roi + 'x' : 'Высокий';
        document.getElementById('best-hypo-benefit').innerText = rec.evidence || 'Основано на открытых данных';
        document.getElementById('best-hypo-kpi').innerText = rec.kpi || '+22% к ресурсу';
        document.getElementById('best-hypo-evidence').innerText = rec.evidence || '12 статей, 4 патента';
    }).catch(e => {
        document.getElementById('best-hypo-title').innerText = 'Рекомендация недоступна';
        const btn = document.getElementById('create-from-rec-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = 'Рекомендация не загружена';
        }
    });
    
    const top = data.top_hypothesis;
    if (top) {
        document.getElementById('best-hypo-title').innerText = top.title || 'Нет гипотез';
        document.getElementById('best-hypo-desc').innerText = top.description || '';
        document.getElementById('best-hypo-object').innerText = top.object_name || '—';
        document.getElementById('best-hypo-roi').innerText = top.roi ? top.roi + 'x' : '—';
        document.getElementById('best-hypo-cost').innerText = top.research_cost ? '$' + top.research_cost : '—';
        document.getElementById('best-hypo-benefit').innerText = top.economic_benefit ? '$' + top.economic_benefit + ' / год' : '—';
    }
    
    const counts = data.status_counts || {};
    document.getElementById('count-status-idea').innerText = counts.idea || 0;
    document.getElementById('count-status-validation').innerText = counts.validation || 0;
    document.getElementById('count-status-experiment').innerText = counts.experiment || 0;
    document.getElementById('count-status-completed').innerText = counts.completed || 0;
    
    const statuses = ['idea', 'validation', 'experiment', 'completed'];
    statuses.forEach(status => {
        const listContainer = document.getElementById(`list-status-${status}`);
        if (listContainer) {
            listContainer.innerHTML = '';
            const items = data.status_lists ? data.status_lists[status] : [];
            if (!items || items.length === 0) {
                listContainer.innerHTML = '<div class="text-xs text-slate-400 text-center py-4">Нет гипотез</div>';
            } else {
                items.forEach(h => {
                    listContainer.innerHTML += `
                        <div class="p-3 bg-slate-50 border border-slate-100 rounded-lg cursor-pointer hover:border-brand/50 hover:bg-white transition-all shadow-sm" onclick="window.switchTab('hypotheses'); window.selectHypothesis(${h.id})">
                            <span class="text-xs font-bold text-slate-800 line-clamp-2">${h.title}</span>
                            <div class="flex justify-between items-center mt-2">
                                <span class="text-[9px] text-slate-400">Новизна: ${h.novelty_score}%</span>
                                <span class="text-[10px] font-bold text-brand">ROI: ${h.roi}x</span>
                            </div>
                        </div>
                    `;
                });
            }
        }
    });
    
    const grid = document.getElementById('dashboard-objects-grid');
    if (grid) {
        grid.innerHTML = '';
        (data.objects || []).forEach(obj => {
            const card = document.createElement('div');
            card.className = "p-4 bg-slate-50 border border-slate-100 rounded-xl hover:border-brand/40 hover:bg-white cursor-pointer transition-all space-y-3";
            card.onclick = () => { window.switchTab('objects'); window.selectObject(obj.id); };
            const metrics = (obj.metrics || []).slice(0, 2);
            card.innerHTML = `
                <div class="flex justify-between items-center">
                    <h4 class="text-xs font-bold text-slate-800 uppercase tracking-wider">${obj.name}</h4>
                    <span class="text-[9px] bg-brand/5 text-brand px-2 py-0.5 rounded-full font-bold">${obj.status}</span>
                </div>
                <p class="text-[11px] text-slate-500 line-clamp-2">${obj.description || ''}</p>
                <div class="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                    ${metrics.map(m => `<div class="text-left"><span class="text-[9px] text-slate-400 block">${m.name}</span><span class="text-xs font-bold text-slate-800">${m.current} <span class="text-[9px] font-normal text-slate-500">-> ${m.target}</span></span></div>`).join('')}
                </div>
            `;
            grid.appendChild(card);
        });
    }
    
    const stats = data.knowledge_stats || {};
    document.querySelectorAll('.kb-stats-papers').forEach(el => el.innerText = stats.papers || 0);
    document.querySelectorAll('.kb-stats-patents').forEach(el => el.innerText = stats.patents || 0);
    document.querySelectorAll('.kb-stats-reports').forEach(el => el.innerText = stats.reports || 0);
    document.querySelectorAll('.kb-stats-datasets').forEach(el => el.innerText = stats.datasets || 0);
}