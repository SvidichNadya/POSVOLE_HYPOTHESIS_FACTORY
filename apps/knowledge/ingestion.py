"""
Модуль для интеллектуального ингеста документов с использованием YandexGPT.
"""

import logging
from typing import Dict, List, Tuple

from django.db import transaction

from apps.knowledge.models import KnowledgeDocument
from apps.graph.models import GraphNode, GraphEdge
from apps.core.yandex_ai import extract_graph_from_text

logger = logging.getLogger(__name__)


def extract_entities_and_relations_ai(text: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Извлечение сущностей и связей из текста с помощью YandexGPT.
    
    Returns:
        (entities, relations)
    """
    if not text or len(text) < 50:
        return [], []
    
    try:
        data = extract_graph_from_text(text)
        entities = data.get('entities', [])
        relations = data.get('relations', [])
        logger.info(f"Извлечено {len(entities)} сущностей и {len(relations)} связей")
        return entities, relations
    except Exception as e:
        logger.error(f"Ошибка извлечения графа: {e}", exc_info=True)
        return [], []


@transaction.atomic
def ingest_document_with_ai(doc_data: Dict, doc_type: str = 'paper') -> KnowledgeDocument:
    """
    Ингест документа с извлечением графа знаний с помощью AI.
    """
    title = doc_data.get('title', 'Без названия')
    abstract = doc_data.get('abstract', '')
    meta = doc_data.get('meta', '')
    tags = doc_data.get('tags', [])

    # Проверка на дубликат по названию
    existing = KnowledgeDocument.objects.filter(title=title).first()
    if existing:
        logger.info(f"Документ уже существует: {title}")
        return existing

    # Создаём документ со статусом "в обработке"
    doc = KnowledgeDocument.objects.create(
        doc_type=doc_type,
        title=title,
        meta=meta,
        abstract=abstract,
        tags=tags,
        status='processing',
        progress=10
    )
    logger.info(f"Создан документ: {title}")

    # Извлечение графа знаний
    if abstract and len(abstract) > 100:
        entities, relations = extract_entities_and_relations_ai(abstract)
        doc.progress = 50
        doc.save(update_fields=['progress'])

        # Добавляем узлы в граф
        for ent in entities:
            text = ent.get('text', '').strip()
            label = ent.get('label', 'param')
            if text:
                node_id = f"ent_{hash(text) % 1000000}"
                GraphNode.objects.get_or_create(
                    node_id=node_id,
                    defaults={
                        'label': text[:100],
                        'node_type': label if label in ['param', 'kpi', 'mech', 'fail'] else 'param',
                        'description': f"Извлечено из: {title}"
                    }
                )

        # Добавляем связи
        for rel in relations:
            subj = rel.get('subject', '').strip()
            obj = rel.get('object', '').strip()
            pred = rel.get('predicate', 'связан с')[:50]

            if subj and obj:
                subj_node, _ = GraphNode.objects.get_or_create(
                    node_id=f"ent_{hash(subj) % 1000000}",
                    defaults={'label': subj[:100], 'node_type': 'param'}
                )
                obj_node, _ = GraphNode.objects.get_or_create(
                    node_id=f"ent_{hash(obj) % 1000000}",
                    defaults={'label': obj[:100], 'node_type': 'param'}
                )
                GraphEdge.objects.get_or_create(
                    source=subj_node,
                    target=obj_node,
                    relation_type=pred,
                    defaults={'color': '#135BEC', 'is_dashed': False}
                )

        doc.progress = 100
        doc.status = 'completed'
        doc.save(update_fields=['progress', 'status'])
        logger.info(f"Граф обновлён для документа {title}")

    else:
        doc.status = 'completed'
        doc.progress = 100
        doc.save(update_fields=['status', 'progress'])
        logger.info(f"Документ {title} обработан без извлечения графа (короткая аннотация)")

    return doc