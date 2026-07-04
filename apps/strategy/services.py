from apps.core.models import ResearchProject
from apps.objects.models import ResearchObject
from apps.hypotheses.models import Hypothesis
from apps.knowledge.models import KnowledgeDocument
from apps.core.yandex_ai import ask_yandex_gpt_json

def get_dashboard_data():
    top_hypo = Hypothesis.objects.order_by('-roi').first()
    top_data = None
    if top_hypo:
        top_data = {
            'id': top_hypo.id,
            'title': top_hypo.title,
            'description': top_hypo.description,
            'object_name': top_hypo.object.name if top_hypo.object else None,
            'roi': top_hypo.roi,
            'research_cost': top_hypo.research_cost,
            'economic_benefit': top_hypo.economic_benefit,
            'novelty_score': top_hypo.novelty_score,
            'feasibility_score': top_hypo.feasibility_score,
            'payback': top_hypo.payback_months,
        }
        
    status_counts = {}
    for status, _ in Hypothesis.STATUS_CHOICES:
        status_counts[status] = Hypothesis.objects.filter(status=status).count()
        
    status_lists = {
        'idea': [],
        'validation': [],
        'experiment': [],
        'completed': []
    }
    
    for h in Hypothesis.objects.all().order_by('-id')[:40]:
        if h.status in status_lists:
            status_lists[h.status].append({
                'id': h.id,
                'title': h.title,
                'roi': h.roi,
                'novelty_score': h.novelty_score
            })
            
    objects_data = []
    for obj in ResearchObject.objects.all()[:4]:
        objects_data.append({
            'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'status': obj.status,
            'metrics': [{'name': m.name, 'current': m.current_value, 'target': m.target_value} for m in obj.metrics.all()[:2]]
        })
        
    kb_stats = {
        'papers': KnowledgeDocument.objects.filter(doc_type='paper').count(),
        'patents': KnowledgeDocument.objects.filter(doc_type='patent').count(),
        'reports': KnowledgeDocument.objects.filter(doc_type='report').count(),
        'datasets': KnowledgeDocument.objects.filter(doc_type='dataset').count(),
    }
    
    return {
        'top_hypothesis': top_data,
        'status_counts': status_counts,
        'status_lists': status_lists,
        'objects': objects_data,
        'knowledge_stats': kb_stats,
    }


def generate_top_recommendation():
    """
    Генерирует новую, ещё не рассмотренную гипотезу на основе существующих объектов,
    гипотез и базы знаний. Если данных мало, использует интернет-поиск через ИИ.
    """
    import logging
    logger = logging.getLogger(__name__)

    objects = ResearchObject.objects.all()
    hypotheses = Hypothesis.objects.all()
    docs = KnowledgeDocument.objects.all()

    context_parts = []
    if objects:
        context_parts.append("Объекты исследования:")
        for obj in objects:
            metrics = ", ".join([f"{m.name}: {m.current_value}->{m.target_value}" for m in obj.metrics.all()])
            context_parts.append(f"- {obj.name}: {metrics}")
    if hypotheses:
        context_parts.append("Существующие гипотезы:")
        for h in hypotheses[:5]:
            context_parts.append(f"- {h.title}: {h.description[:100]}")
    if docs:
        context_parts.append("База знаний:")
        for d in docs[:5]:
            context_parts.append(f"- {d.title}: {d.abstract[:100]}")

    context = "\n".join(context_parts) if context_parts else "Нет данных."

    system_prompt = """Ты — стратегический R&D аналитик. На основе предоставленного контекста предложи одну наиболее перспективную гипотезу для исследования, которая ещё не была рассмотрена. Если контекст пуст, предложи гипотезу, основанную на мировых трендах в материаловедении, энергетике или биотехнологиях.

Верни ответ в формате JSON:
{
  "title": "Название гипотезы",
  "description": "Описание гипотезы (2-3 предложения)",
  "object_name": "Название объекта, к которому относится гипотеза (если применимо, иначе 'Новая область')",
  "roi": ожидаемый ROI (число, например 3.5),
  "research_cost": ожидаемая стоимость НИОКР (число в долларах),
  "economic_benefit": ожидаемый годовой экономический эффект (число в долларах),
  "payback_months": ожидаемый срок окупаемости в месяцах (целое число),
  "novelty_score": оценка новизны от 0 до 100 (целое число),
  "feasibility_score": оценка реализуемости от 0 до 1 (число)
}
"""

    user_prompt = f"Контекст:\n{context}"
    result = ask_yandex_gpt_json(system_prompt, user_prompt, temperature=0.7)
    if not result:
        # fallback, если AI не ответил
        result = {
            "title": "Перспективное направление: графеновые нанокомпозиты",
            "description": "Разработка новых композитных материалов на основе графена для повышения прочности и проводимости.",
            "object_name": "Графеновые композиты",
            "roi": 4.2,
            "research_cost": 200000,
            "economic_benefit": 800000,
            "payback_months": 10,
            "novelty_score": 85,
            "feasibility_score": 0.7
        }
    return result