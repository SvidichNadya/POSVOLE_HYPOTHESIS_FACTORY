import logging
import re
from typing import Optional
from django.db import transaction

from .models import Hypothesis, Evidence, RoadmapStep
from apps.objects.models import ResearchObject
from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.ingestion import ingest_document_with_ai
from .engine import RndStrategyEngine

logger = logging.getLogger(__name__)

def search_internet(query: str) -> list:
    """Выполняет свободный поиск данных в интернете (DuckDuckGo)."""
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=5)
        return [f"[Web Search] {r.get('title', '')}: {r.get('body', '')} (URL: {r.get('href', '')})" for r in results]
    except Exception as e:
        logger.warning(f"Ошибка поиска в интернете DDG: {e}")
        return []

def search_knowledge_base(query: str) -> list:
    """Поиск в локальной базе знаний."""
    try:
        docs = KnowledgeDocument.objects.filter(
            abstract__icontains=query
        )[:5]
        results = []
        for doc in docs:
            results.append(f"[Knowledge Base] {doc.title}: {doc.abstract[:300]}... (Источник: {doc.meta or 'Внутренняя база'})")
        return results
    except Exception as e:
        logger.warning(f"Ошибка поиска в базе знаний: {e}")
        return []

def generate_hypothesis(object_id, kpi_target, kpi_val, budget, duration, approach, team):
    obj = ResearchObject.objects.filter(id=object_id).first() if object_id else None
    engine = RndStrategyEngine()
    
    novelty = engine.calculate_combinatorial_novelty(approach)
    docs_count = KnowledgeDocument.objects.count()
    feasibility = engine.calculate_feasibility(team, docs_count)
    
    economic_benefit_yearly = (budget * 3.5) if budget else 1000000
    rnpv, roi, payback = engine.calculate_rnpv(budget or 0, economic_benefit_yearly, duration or 6, feasibility)
    complexity = engine.analyze_complexity_gert(duration or 6, team)
    
    object_name = obj.name if obj else "Научная задача"
    
    # 1. Защита от мусорного ввода при поиске
    is_garbage = bool(re.match(r'^([a-zA-Zа-яА-Я0-9])\1*$', approach.strip())) or len(approach.strip()) < 5
    search_approach = "" if is_garbage else approach
    keywords = search_approach[:50] if search_approach else kpi_target
    
    # 2. Собираем контекст из базы знаний
    context_texts = []
    
    # Локальный поиск
    kb_results = search_knowledge_base(keywords)
    context_texts.extend(kb_results)
    
    # Поиск в интернете
    search_query = f"научные исследования {object_name} {kpi_target} {search_approach}".strip()
    logger.info(f"Поиск в сети: {search_query}")
    web_results = search_internet(search_query)
    context_texts.extend(web_results)
    
    # 3. ИИ генерация с контекстом
    ai_data = engine.generate_ai_hypothesis(
        object_name=object_name,
        target_kpi=kpi_target or "целевой показатель",
        expected_improvement=kpi_val or "улучшение",
        approach=approach,
        context_docs=context_texts
    )
    
    title_kpi = kpi_target if kpi_target else "целевого процесса"
    
    hypo = Hypothesis.objects.create(
        object=obj,
        title=ai_data.get('title', f"Оптимизация {title_kpi} через передовые методы"),
        description=ai_data.get('description', f"Предлагается улучшить {title_kpi}."),
        status='idea',
        novelty_score=novelty,
        feasibility_score=feasibility,
        research_cost=budget or 0,
        economic_benefit=economic_benefit_yearly,
        payback_months=payback or 12,
        roi=roi or 0.0,
        complexity_data=complexity
    )
    
    # 4. Формируем доказательства с источниками
    evidences = ai_data.get('evidences', [])
    if not evidences:
        evidences = engine.generate_xai_evidence_chain(object_name, approach)
    
    ev_texts = []
    for ev in evidences:
        t = ev.get('text', 'Обоснование не указано')
        s = ev.get('source', 'Аналитическая система')
        Evidence.objects.create(hypothesis=hypo, text=t, source=s)
        ev_texts.append(t)
    
    # 5. Дорожная карта
    RoadmapStep.objects.create(hypothesis=hypo, name="Фаза 1: Лабораторная проверка", duration="1 мес.", risk_level="Низкий", order=1)
    RoadmapStep.objects.create(hypothesis=hypo, name="Фаза 2: MVP прототип", duration=f"{(duration or 6) - 1} мес.", risk_level="Высокий" if feasibility < 0.6 else "Средний", order=2)
    
    # 6. Сохранение гипотезы в базу знаний
    if len(hypo.description) > 30:
        try:
            ingest_document_with_ai({
                'title': f"Гипотеза: {hypo.title[:100]}",
                'abstract': hypo.description + "\nДоказательства: " + " ".join(ev_texts),
                'meta': 'Синтезировано автоматически',
                'tags': ['Hypothesis', 'Generated']
            }, doc_type='report')
        except Exception as e:
            logger.error(f"Не удалось извлечь граф из гипотезы: {e}")
            
    return hypo