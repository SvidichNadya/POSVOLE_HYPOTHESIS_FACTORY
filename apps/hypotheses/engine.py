"""
Ядро R&D Strategy Engine с интеграцией Yandex AI Studio.
"""

import math
import logging
from typing import Dict, Any, List, Optional

from django.db.models import Count
from apps.graph.models import GraphNode, GraphEdge
from apps.knowledge.models import KnowledgeDocument
from apps.core.yandex_ai import generate_hypothesis_text, ask_yandex_gpt_json

logger = logging.getLogger(__name__)


class RndStrategyEngine:
    """Движок для расчёта научных и бизнес-показателей."""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.risk_free_rate = 0.08  # 8% базовая ставка дисконтирования
    
    # ========== СЛОЙ 5: КОМБИНАТОРНАЯ НОВИЗНА ==========
    
    def calculate_combinatorial_novelty(self, approach_text: str) -> int:
        """
        Расчёт комбинаторной новизны (Z-score proxy).
        
        Анализирует, насколько редки комбинации сущностей из подхода в существующем графе.
        """
        if not approach_text:
            return 50
        
        # Находим узлы графа, упомянутые в тексте
        matched_nodes = []
        for node in GraphNode.objects.all():
            if node.label.lower() in approach_text.lower():
                matched_nodes.append(node)
        
        if len(matched_nodes) < 2:
            return 70  # Базовая новизна для новых концептов
        
        # Считаем плотность связей между найденными узлами
        existing_edges = GraphEdge.objects.filter(
            source__in=matched_nodes,
            target__in=matched_nodes
        ).count()
        
        possible_edges = len(matched_nodes) * (len(matched_nodes) - 1)
        density = existing_edges / possible_edges if possible_edges > 0 else 1
        
        # Чем ниже плотность, тем выше новизна
        z_score_proxy = (1.0 - density) * 100
        return int(max(40, min(98, z_score_proxy)))
    
    # ========== СЛОЙ 6: РЕАЛИЗУЕМОСТЬ (DARPA SCORE) ==========
    
    def calculate_feasibility(self, team_data: Dict[str, Any], docs_count: int) -> float:
        """
        Оценка реализуемости на основе команды и объёма знаний.
        """
        scientists = team_data.get('scientists', 0)
        engineers = team_data.get('engineers', 0)
        equipment = team_data.get('equipment', 'mid')
        
        # Научный и инженерный потенциал
        sci_cap = scientists * 1.5
        eng_cap = engineers * 1.2
        
        # Оснащённость
        eq_multiplier = {
            'high': 1.2,
            'mid': 1.0,
            'low': 0.8
        }.get(equipment, 1.0)
        
        team_score = (sci_cap + eng_cap) * eq_multiplier
        
        # Вклад от базы знаний (максимум 0.5)
        base_prob = 0.3 + (min(docs_count, 10) * 0.02)
        
        # Вклад от команды (максимум 0.4)
        team_prob = min(team_score / 20.0, 0.4)
        
        return round(min(0.95, base_prob + team_prob), 2)
    
    # ========== СЛОЙ 7: ЭКОНОМИЧЕСКАЯ ОЦЕНКА (rNPV) ==========
    
    def calculate_rnpv(
        self,
        research_cost: float,
        economic_benefit: float,
        duration_months: int,
        feasibility: float
    ) -> tuple:
        """
        Расчёт Risk-adjusted NPV, ROI и срока окупаемости.
        """
        if not research_cost or not economic_benefit:
            return 0.0, 0.0, 0
        
        years = duration_months / 12.0
        
        # Дисконтирование затрат (равномерные траты)
        discounted_cost = research_cost / ((1 + self.risk_free_rate) ** (years / 2))
        
        # Дисконтирование выгод с учётом вероятности успеха
        # Горизонт отдачи — 3 года после НИОКР
        discounted_benefit = (economic_benefit * 3 * feasibility) / (
            (1 + self.risk_free_rate) ** (years + 1.5)
        )
        
        rnpv = discounted_benefit - discounted_cost
        roi = round(discounted_benefit / discounted_cost, 2) if discounted_cost > 0 else 0
        payback = int(math.ceil((research_cost / economic_benefit) * 12)) if economic_benefit > 0 else 0
        
        return round(rnpv, 2), roi, payback
    
    # ========== СЛОЙ 8: GERT-СЛОЖНОСТЬ ==========
    
    def analyze_complexity_gert(self, duration_months: int, team_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Оценка организационной и ресурсной сложности (GERT).
        """
        scientists = team_data.get('scientists', 1) or 1
        equipment = team_data.get('equipment', 'mid')
        
        sci = min(10, max(2, int(12 / scientists)))
        tech = 8 if equipment == 'low' else 4
        res = min(10, duration_months // 2)
        org = min(10, (sci + tech) // 2)
        
        return {
            'sci': sci,
            'tech': tech,
            'res': res,
            'org': org
        }
    
    # ========== СЛОЙ 9: XAI + ГЕНЕРАЦИЯ ГИПОТЕЗЫ (YandexGPT) ==========
    
    def generate_ai_hypothesis(
            self,
            object_name: str,
            target_kpi: str,
            expected_improvement: str,
            approach: str,
            context_docs: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Генерация научно-обоснованной гипотезы с использованием YandexGPT.
            """
            if not context_docs:
                context_docs = []
                keywords = approach[:50] if approach and len(approach) > 3 else target_kpi
                docs = KnowledgeDocument.objects.filter(abstract__icontains=keywords)[:3]
                for doc in docs:
                    context_docs.append(f"{doc.title}: {doc.abstract[:200]}... (Источник: {doc.meta or 'Внутренняя база'})")
            
            return generate_hypothesis_text(
                object_name=object_name or "Неизвестный объект",
                target_kpi=target_kpi or "целевой показатель",
                expected_improvement=expected_improvement or "улучшение",
                approach=approach or "поиск оптимального решения",
                context_docs=context_docs
            )
    
    def generate_xai_evidence_chain(
        self,
        object_name: str,
        approach: str
    ) -> List[Dict[str, str]]:
        """
        Генерация цепочки доказательств (XAI) на основе графа и базы знаний с реальными ссылками.
        """
        evidences = []
        
        # 1. Ищем документы по ключевым словам в базе знаний
        keywords = approach[:50] if approach else object_name
        docs = KnowledgeDocument.objects.filter(
            abstract__icontains=keywords
        )[:3]
        
        for doc in docs:
            source = doc.meta or "Внутренняя база знаний"
            # Если есть ссылка на DOI или URL в метаданных
            if doc.meta and ('doi' in doc.meta.lower() or 'http' in doc.meta.lower()):
                source = doc.meta
            evidences.append({
                'text': f"Концепт подтверждён в литературе: {doc.abstract[:150]}...",
                'source': source
            })
        
        # 2. Если документов мало, добавляем вывод из графа
        if len(evidences) < 2:
            # Ищем связанные узлы в графе
            related_nodes = GraphNode.objects.filter(
                label__icontains=approach[:30]
            )[:3]
            
            if related_nodes:
                node_names = ", ".join([n.label for n in related_nodes])
                evidences.append({
                    'text': f"Обнаружена связь между концептами: {node_names}",
                    'source': "Граф знаний (анализ связей)"
                })
        
        # 3. Добавляем поиск в интернете для получения актуальных ссылок
        if len(evidences) < 3:
            try:
                from apps.hypotheses.services import search_internet
                search_query = f"{object_name} {approach[:30]} research paper".strip()
                web_results = search_internet(search_query)
                for result in web_results[:2]:
                    # Извлекаем URL из результата
                    import re
                    url_match = re.search(r'URL:\s*(https?://[^\s)]+)', result)
                    source = url_match.group(1) if url_match else "Веб-источник"
                    evidences.append({
                        'text': f"Актуальное исследование: {result[:150]}...",
                        'source': source
                    })
            except Exception as e:
                logger.warning(f"Ошибка поиска в интернете для XAI: {e}")
        
        # 4. Если всё ещё пусто, добавляем базовое обоснование с DOI
        if not evidences:
            evidences.append({
                'text': f"Предлагаемый подход {approach[:50]}... основан на фундаментальных физико-химических принципах.",
                'source': "Фундаментальные научные принципы"
            })
        
        return evidences