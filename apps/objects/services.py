"""
Сервисы для работы с объектами исследования, включая What-If симуляцию.
"""

import logging
from typing import Dict, Any

from .models import ResearchObject
from apps.core.yandex_ai import predict_what_if

logger = logging.getLogger(__name__)


def get_object_dashboard_data(obj_id: int) -> Dict[str, Any]:
    """
    Получение данных объекта для дашборда.
    """
    try:
        obj = ResearchObject.objects.get(id=obj_id)
    except ResearchObject.DoesNotExist:
        return None
    
    return {
        'id': obj.id,
        'name': obj.name,
        'description': obj.description,
        'status': obj.status,
        'metrics': [
            {
                'name': m.name,
                'current': m.current_value,
                'target': m.target_value,
                'unit': m.unit
            }
            for m in obj.metrics.all()
        ],
        'bottlenecks': [{'description': b.description} for b in obj.bottlenecks.all()],
        'strengths': [{'description': s.description} for s in obj.strengths.all()],
        'sliders': [
            {
                'key': s.key,
                'name': s.name,
                'min': s.min_value,
                'max': s.max_value,
                'step': s.step,
                'default': s.default_value,
                'unit': s.unit
            }
            for s in obj.sliders.all()
        ],
    }


def simulate_what_if(obj_id: int, slider_values: Dict[str, float]) -> Dict[str, str]:
    """
    What-If симуляция с использованием YandexGPT для физического прогноза.
    
    Args:
        obj_id: ID объекта
        slider_values: словарь с новыми значениями параметров
        
    Returns:
        Словарь с прогнозируемыми значениями KPI (kpi1-kpi4) в виде строк
    """
    try:
        obj = ResearchObject.objects.get(id=obj_id)
    except ResearchObject.DoesNotExist:
        logger.warning(f"Объект {obj_id} не найден")
        return {f'kpi{i}': '—' for i in range(1, 5)}
    
    # Формируем текущее состояние
    metrics = list(obj.metrics.all())
    sliders = list(obj.sliders.all())
    
    current_state = ", ".join([
        f"{m.name}: {m.current_value}" for m in metrics[:4]
    ])
    
    # Формируем описание изменений
    changes = []
    for slider in sliders:
        new_val = slider_values.get(slider.key, slider.default_value)
        if new_val != slider.default_value:
            changes.append(
                f"'{slider.name}' изменён с {slider.default_value} на {new_val} {slider.unit or ''}"
            )
    
    if not changes:
        changes.append("Изменений нет")
    
    slider_changes = ", ".join(changes)
    
    # Вызываем AI для прогноза
    try:
        result = predict_what_if(
            object_name=obj.name,
            current_metrics=current_state,
            slider_changes=slider_changes,
            approach=obj.description or ""
        )
        logger.info(f"What-If симуляция для {obj.name}: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка What-If симуляции: {e}", exc_info=True)
        
        # Fallback: математическая эмуляция
        return _fallback_simulation(metrics, sliders, slider_values)


def _fallback_simulation(metrics, sliders, slider_values) -> Dict[str, str]:
    """
    Резервная математическая симуляция на случай ошибки AI.
    """
    result = {}
    
    # Вычисляем совокупный фактор изменения
    total_delta = 0
    for slider in sliders:
        val = slider_values.get(slider.key, slider.default_value)
        if slider.default_value != 0:
            delta = (val - slider.default_value) / slider.default_value
            total_delta += delta * 0.5
    
    # Применяем к метрикам
    for i, metric in enumerate(metrics[:4]):
        try:
            import re
            numbers = re.findall(r'[\d.]+', metric.current_value)
            if numbers:
                base_val = float(numbers[0])
                unit = metric.current_value.replace(numbers[0], '')
                impact = 1 if i % 2 == 0 else -0.8
                new_val = base_val * (1 + total_delta * impact)
                result[f'kpi{i+1}'] = f"{round(new_val, 1)}{unit}"
            else:
                result[f'kpi{i+1}'] = metric.current_value
        except Exception:
            result[f'kpi{i+1}'] = metric.current_value
    
    # Заполняем недостающие слоты
    for i in range(len(metrics) + 1, 5):
        result[f'kpi{i}'] = "—"
    
    return result