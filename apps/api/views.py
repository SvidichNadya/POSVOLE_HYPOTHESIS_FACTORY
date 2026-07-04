import json
import logging
import threading
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from apps.core.models import ResearchProject
from apps.core.serializers import ResearchProjectSerializer
from apps.core.yandex_ai import generate_project_plan, generate_object_recommendation, generate_top_recommendation

from apps.objects.models import ResearchObject, Metric
from apps.objects.serializers import ResearchObjectSerializer
from apps.objects.services import get_object_dashboard_data, simulate_what_if as sim_service

from apps.hypotheses.models import Hypothesis
from apps.hypotheses.serializers import HypothesisSerializer
from apps.hypotheses.services import generate_hypothesis as gen_hypo

from apps.knowledge.models import KnowledgeDocument
from apps.knowledge.serializers import KnowledgeDocumentSerializer
from apps.knowledge.services import search_documents, search_internet_bulk
from apps.knowledge.ingestion import ingest_document_with_ai

from apps.graph.models import GraphNode, GraphEdge
from apps.graph.serializers import GraphNodeSerializer, GraphEdgeSerializer
from apps.graph.services import get_graph_data
from apps.strategy.services import get_dashboard_data

logger = logging.getLogger(__name__)

def dashboard(request):
    data = get_dashboard_data()
    # Генерируем контекст для топ-рекомендации
    context_parts = []
    objects = ResearchObject.objects.all()
    hypotheses = Hypothesis.objects.all()
    docs = KnowledgeDocument.objects.all()
    
    if objects:
        context_parts.append("Объекты:")
        for obj in objects:
            metrics = ", ".join([f"{m.name}: {m.current_value}->{m.target_value}" for m in obj.metrics.all()])
            context_parts.append(f"- {obj.name} ({metrics})")
    if hypotheses:
        context_parts.append("Гипотезы:")
        for h in hypotheses[:5]:
            context_parts.append(f"- {h.title}")
    if docs:
        context_parts.append("Документы:")
        for d in docs[:5]:
            context_parts.append(f"- {d.title}")
    
    context = "\n".join(context_parts) if context_parts else "Нет данных."
    data['top_recommendation'] = generate_top_recommendation(context)
    return JsonResponse(data)

@csrf_exempt
def dashboard_recommendation(request):
    """Отдельный эндпоинт для получения только топ-рекомендации"""
    context_parts = []
    objects = ResearchObject.objects.all()
    hypotheses = Hypothesis.objects.all()
    docs = KnowledgeDocument.objects.all()
    
    if objects:
        context_parts.append("Объекты:")
        for obj in objects:
            metrics = ", ".join([f"{m.name}: {m.current_value}->{m.target_value}" for m in obj.metrics.all()])
            context_parts.append(f"- {obj.name} ({metrics})")
    if hypotheses:
        context_parts.append("Гипотезы:")
        for h in hypotheses[:5]:
            context_parts.append(f"- {h.title}")
    if docs:
        context_parts.append("Документы:")
        for d in docs[:5]:
            context_parts.append(f"- {d.title}")
    
    context = "\n".join(context_parts) if context_parts else "Нет данных."
    rec = generate_top_recommendation(context)
    return JsonResponse(rec)

def projects_list(request):
    projects = ResearchProject.objects.all().order_by('-id')
    return JsonResponse(ResearchProjectSerializer(projects, many=True).data, safe=False)

def project_detail(request, pk):
    proj = get_object_or_404(ResearchProject, pk=pk)
    return JsonResponse(ResearchProjectSerializer(proj).data)

@csrf_exempt
@require_http_methods(["POST"])
def create_project(request):
    try:
        data = json.loads(request.body)
        obj_id = data.get('object_id')
        hypo_id = data.get('hypothesis_id')

        obj = ResearchObject.objects.filter(id=obj_id).first() if obj_id else None
        hypo = Hypothesis.objects.filter(id=hypo_id).first() if hypo_id else None

        obj_name = obj.name if obj else "Не определен"
        hypo_desc = hypo.description if hypo else "Исследование с нуля"

        # ИИ АВТОМАТИЧЕСКИ ГЕНЕРИРУЕТ ВЕСЬ ПРОЕКТ
        plan = generate_project_plan(
            data.get('name'),
            obj_name,
            hypo_desc,
            data.get('available_resources', 'Нет данных')
        )

        project = ResearchProject.objects.create(
            name=data.get('name', 'Новый проект'),
            description=data.get('description', ''),
            object=obj,
            hypothesis=hypo,
            available_resources=data.get('available_resources', ''),
            checklist=plan.get('checklist', []),
            success_probability=plan.get('success_probability', 50) / 100.0,
            optimal_scenario=plan.get('optimal_scenario', ''),
            pessimistic_scenario=plan.get('pessimistic_scenario', ''),
            optimistic_scenario=plan.get('optimistic_scenario', ''),
            risks=plan.get('risks', ''),
            risk_mitigation=plan.get('risk_mitigation', ''),
            analogs=plan.get('analogs', ''),
            resources_needed=plan.get('resources_needed', ''),
            business_roi=plan.get('business_roi', 0.0),
            business_cost=plan.get('business_cost', 0),
            business_payback=plan.get('business_payback', 0)
        )
        return JsonResponse({'id': project.id, 'status': 'created'})
    except Exception as e:
        logger.error(f"Create project error: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_project_checklist(request, pk):
    """Обновляет чек-лист проекта и автоматически меняет статус/прогресс"""
    try:
        data = json.loads(request.body)
        project = get_object_or_404(ResearchProject, pk=pk)
        project.checklist = data.get('checklist', project.checklist)

        # Авторасчет прогресса
        total = len(project.checklist)
        done = sum(1 for item in project.checklist if item.get('done'))
        project.progress = int((done / total * 100)) if total > 0 else 0

        if project.progress == 0:
            project.status = 'planning'
        elif project.progress == 100:
            project.status = 'completed'
        else:
            project.status = 'active'

        project.save()
        return JsonResponse({'status': 'updated', 'progress': project.progress, 'project_status': project.status})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_metric(request, pk):
    """Редактирование KPI пользователем"""
    try:
        data = json.loads(request.body)
        metric = get_object_or_404(Metric, pk=pk)
        if 'current_value' in data:
            metric.current_value = data['current_value']
        if 'target_value' in data:
            metric.target_value = data['target_value']
        metric.save()
        return JsonResponse({'status': 'updated'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def object_ai_recommendation(request, pk):
    """Возвращает ИИ-рекомендацию для объекта"""
    obj = get_object_or_404(ResearchObject, pk=pk)
    metrics = ", ".join([f"{m.name} ({m.current_value} -> {m.target_value})" for m in obj.metrics.all()])
    bnecks = ", ".join([b.description for b in obj.bottlenecks.all()])
    rec_text = generate_object_recommendation(obj.name, metrics, bnecks)
    return JsonResponse({'recommendation': rec_text})

def objects_list(request):
    objects = ResearchObject.objects.all()
    return JsonResponse(ResearchObjectSerializer(objects, many=True).data, safe=False)

def object_detail(request, pk):
    data = get_object_dashboard_data(pk)
    if data:
        return JsonResponse(data)
    return JsonResponse({'error': 'Object not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def create_object(request):
    try:
        data = json.loads(request.body)
        project, _ = ResearchProject.objects.get_or_create(name='Общая база')
        obj = ResearchObject.objects.create(
            project=project,
            name=data.get('name', 'Без названия'),
            description=data.get('description', ''),
            status='Новый'
        )
        for m in data.get('metrics', []):
            Metric.objects.create(
                object=obj,
                name=m.get('name', ''),
                current_value=m.get('current_value', ''),
                target_value=m.get('target_value', '')
            )
        return JsonResponse({'id': obj.id, 'status': 'created'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def hypotheses_list(request):
    hypotheses = Hypothesis.objects.all().order_by('-id')
    return JsonResponse(HypothesisSerializer(hypotheses, many=True).data, safe=False)

def hypothesis_detail(request, pk):
    hypo = get_object_or_404(Hypothesis, pk=pk)
    return JsonResponse(HypothesisSerializer(hypo).data)

@csrf_exempt
@require_http_methods(["POST"])
def generate_hypothesis(request):
    try:
        data = json.loads(request.body)
        object_id = data.get('object_id')
        object_id = int(object_id) if object_id else None
        budget = float(data.get('budget')) if data.get('budget') else None
        duration = int(data.get('duration')) if data.get('duration') else None
        kpi_target = data.get('custom_kpi', 'Пользовательский KPI') if data.get('kpi_target', '') in ['', 'custom'] else data.get('kpi_target', '')

        hypo = gen_hypo(
            object_id,
            kpi_target,
            data.get('kpi_val', ''),
            budget,
            duration,
            data.get('approach', 'Без описания'),
            data.get('team', {})
        )
        return JsonResponse(HypothesisSerializer(hypo).data)
    except Exception as e:
        logger.error(f"Generate hypo error: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_hypothesis_status(request, pk):
    try:
        data = json.loads(request.body)
        hypo = get_object_or_404(Hypothesis, pk=pk)
        hypo.status = data.get('status')
        hypo.save()
        return JsonResponse({'status': 'updated'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def knowledge_list(request):
    doc_type = request.GET.get('type', 'all')
    query = request.GET.get('q', '')
    qs = search_documents(query, doc_type)
    return JsonResponse(KnowledgeDocumentSerializer(qs, many=True).data, safe=False)

def _background_web_ingest(query, filters, doc_type):
    try:
        results = search_internet_bulk(query, filters)
        for i, r in enumerate(results):
            doc_data = {
                'title': r.get('title', f'Web Источник {i+1}')[:250],
                'abstract': f"{r.get('body', '')}\n\nИсточник: {r.get('href', '')}",
                'meta': 'Web Agent',
                'tags': ['web_search']
            }
            try:
                ingest_document_with_ai(doc_data, doc_type)
            except Exception as e:
                logger.error(f"Async ingest error for doc: {e}")
    finally:
        connection.close()

@csrf_exempt
@require_http_methods(["POST"])
def create_knowledge(request):
    try:
        doc_type = request.POST.get('doc_type', 'paper')
        title = request.POST.get('title', '')
        meta = request.POST.get('meta', '')
        source_type = request.POST.get('source_type', 'file')
        external_path = request.POST.get('external_path', '')
        uploaded_file = request.FILES.get('file')

        if source_type == 'web' and external_path:
            filters = {
                'fresh_only': request.POST.get('fresh_only') == 'true',
                'verified_only': request.POST.get('verified_only') == 'true',
                'exact_match': request.POST.get('exact_match') == 'true'
            }
            thread = threading.Thread(target=_background_web_ingest, args=(external_path, filters, doc_type))
            thread.start()
            return JsonResponse({'id': 0, 'status': 'processing', 'message': 'Асинхронный поиск запущен. Источники скоро появятся в библиотеке.'})

        abstract = ""
        if source_type == 'file' and uploaded_file:
            try:
                abstract = uploaded_file.read().decode('utf-8', errors='ignore')[:5000]
            except Exception:
                abstract = "Загружен бинарный файл."

        doc_data = {
            'title': title or (uploaded_file.name if uploaded_file else "Новый источник"),
            'abstract': abstract,
            'meta': meta,
            'tags': ['file']
        }

        doc = ingest_document_with_ai(doc_data, doc_type)
        return JsonResponse({'id': doc.id, 'status': doc.status, 'message': 'Документ проанализирован ИИ и добавлен в граф знаний.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def graph_nodes(request):
    return JsonResponse(GraphNodeSerializer(GraphNode.objects.all(), many=True).data, safe=False)

def graph_edges(request):
    return JsonResponse(GraphEdgeSerializer(GraphEdge.objects.all(), many=True).data, safe=False)

@csrf_exempt
def simulate_what_if(request):
    try:
        data = json.loads(request.body)
        result = sim_service(int(data.get('object_id')), data.get('sliders', {}))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def opportunity_map(request):
    g = get_graph_data()
    return JsonResponse({'nodes': g['nodes'], 'edges': g['links'], 'white_spots': [e for e in g['links'] if e.get('dash')]})