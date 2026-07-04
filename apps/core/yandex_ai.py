"""
Модуль интеграции с Yandex AI Studio (актуальный SDK).
Использует yandex-ai-studio-sdk для работы с YandexGPT.
"""

import os
import json
import logging
import re
from typing import Optional, Dict, Any, List
from pathlib import Path

from dotenv import load_dotenv
from yandex_ai_studio_sdk import AIStudio

# Загружаем .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

logger = logging.getLogger(__name__)

# Конфигурация
API_KEY = os.getenv('YANDEX_API_KEY')
FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
MODEL_NAME = os.getenv('YANDEX_MODEL', 'yandexgpt')

_sdk: Optional[AIStudio] = None

def get_sdk() -> AIStudio:
    """Получить экземпляр SDK (ленивая инициализация)."""
    global _sdk
    if _sdk is None:
        if not API_KEY or not FOLDER_ID:
            raise ValueError("YANDEX_API_KEY и YANDEX_FOLDER_ID должны быть заданы в .env")
        _sdk = AIStudio(auth=API_KEY, folder_id=FOLDER_ID)
        logger.info("Yandex AI Studio SDK инициализирован")
    return _sdk

def ask_yandex_gpt(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    json_mode: bool = False
) -> str:
    """Отправить запрос к YandexGPT и получить текстовый ответ."""
    try:
        sdk = get_sdk()
        model = sdk.models.completions(MODEL_NAME).configure(
            temperature=temperature,
            max_tokens=max_tokens,
        )
        messages = [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt},
        ]
        if json_mode:
            messages[0]["text"] += (
                "\n\nВерни ответ СТРОГО в формате валидного JSON. "
                "Не используй markdown-обёртки (```json)."
            )
        result = model.run(messages)
        if result and hasattr(result, 'alternatives') and result.alternatives:
            alt = result.alternatives[0]
            text = ""
            if hasattr(alt, 'message') and hasattr(alt.message, 'text'):
                text = alt.message.text
            elif hasattr(alt, 'text'):
                text = alt.text
            else:
                text = str(alt)
            if json_mode:
                text = _clean_json_response(text)
            return text
        else:
            logger.error("Пустой ответ от YandexGPT")
            return ""
    except Exception as e:
        logger.error(f"Ошибка при запросе к YandexGPT: {e}", exc_info=True)
        return ""

def _clean_json_response(text: str) -> str:
    """Очищает ответ от markdown-обёрток и лишних символов."""
    text = text.replace("```json", "").replace("```", "").strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return text

def ask_yandex_gpt_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> Dict[str, Any]:
    """Отправить запрос и получить ответ в виде JSON."""
    response = ask_yandex_gpt(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=True
    )
    if not response:
        return {}
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return {}

def generate_hypothesis_text(
    object_name: str,
    target_kpi: str,
    expected_improvement: str,
    approach: str,
    context_docs: List[str] = None
) -> Dict[str, Any]:
    """Генерация научно-обоснованной гипотезы с защитой от мусорных данных."""
    context_text = ""
    if context_docs:
        context_text = "\n".join([f"- {doc}" for doc in context_docs[:4]])

    system_prompt = """Ты — ведущий научный эксперт в области материаловедения, химии и физики.
Твоя задача — сгенерировать научно-обоснованную гипотезу для R&D-проекта.

Твой ответ должен содержать СТРОГО валидный JSON:
1. title — точное и лаконичное название гипотезы (до 80 символов)
2. description — развёрнутое научное описание физико-химического механизма (3-5 предложений)
3. evidences — массив из 2-3 доказательств с полями:
   - text: текст доказательства
   - source: ссылка на источник (DOI, URL или название базы данных/статьи)
   ВАЖНО: Каждое доказательство ДОЛЖНО содержать реальную ссылку на источник!
   Используй DOI (например, 10.1016/j.matlet.2024.1352), URL или название конкретной статьи/патента.

ВНИМАНИЕ: Если "Предлагаемый подход" содержит бессмысленный набор букв (например "sdsd", "asd", "123") или совершенно не относится к науке, ПОЛНОСТЬЮ проигнорируй его! В этом случае САМОСТОЯТЕЛЬНО придумай наиболее перспективный научно-обоснованный метод для решения задачи, опираясь на контекст и поиск."""

    user_prompt = f"""
Объект исследования: {object_name}
Целевой KPI: улучшить {target_kpi} на {expected_improvement}
Предлагаемый подход: {approach}

Контекст из научной литературы и интернета:
{context_text if context_text else 'Нет прямых данных. Используй фундаментальные научные знания.'}

Сформируй гипотезу. Для каждого доказательства ОБЯЗАТЕЛЬНО укажи реальную ссылку (DOI, URL или название источника).
"""
    return ask_yandex_gpt_json(system_prompt, user_prompt, temperature=0.4)

def predict_what_if(
    object_name: str,
    current_metrics: str,
    slider_changes: str,
    approach: str = ""
) -> Dict[str, str]:
    """
    Предиктивная симуляция What-If с использованием YandexGPT.
    Возвращает словарь с ключами kpi1, kpi2, kpi3, kpi4 и строковыми значениями.
    """
    system_prompt = """Ты — экспертная физико-математическая модель для прогнозирования свойств материалов.
На основе изменений параметров технологии предскажи новые значения ключевых показателей.

Верни JSON с полями kpi1, kpi2, kpi3, kpi4.
Каждое значение должно быть простой строкой с числом и единицами измерения, например "250 МПа" или "не изменилось".
Не используй вложенные объекты!"""

    user_prompt = f"""
Объект: {object_name}
Текущие метрики: {current_metrics}
Вносимые изменения: {slider_changes}
{approach}

Рассчитай физически обоснованные новые значения для всех метрик.
Учти взаимосвязи между параметрами (например, повышение прочности может снизить пластичность).
"""
    result = ask_yandex_gpt_json(system_prompt, user_prompt, temperature=0.1)
    
    # Принудительно преобразуем все значения в строки, даже если пришли объекты
    final_res = {}
    for i in range(1, 5):
        k = f'kpi{i}'
        val = result.get(k)
        if val is None:
            final_res[k] = "—"
        elif isinstance(val, dict):
            # Если вдруг пришёл объект, пытаемся извлечь value и unit
            value = val.get('value', '')
            unit = val.get('unit', '')
            final_res[k] = f"{value} {unit}".strip() if value else "—"
        elif isinstance(val, (int, float)):
            final_res[k] = str(val)
        elif isinstance(val, str):
            final_res[k] = val
        else:
            final_res[k] = "—"
    return final_res

def extract_graph_from_text(text: str) -> Dict[str, List]:
    """Извлечение графа знаний из научного текста."""
    system_prompt = """Система извлечения графов. Верни JSON:
{"entities": [{"text": "название", "label": "param|kpi|mech|material"}], "relations": [{"subject": "сущность 1", "predicate": "как влияет", "object": "сущность 2"}]}"""
    return ask_yandex_gpt_json(system_prompt, f"Текст:\n{text[:4000]}", temperature=0.2)

def generate_project_plan(project_name: str, object_name: str, hypothesis_desc: str, resources: str) -> Dict[str, Any]:
    """ИИ полностью рассчитывает проект, риски, экономику и чек-лист с конкретными аналогами."""
    system_prompt = """Ты — директор R&D проектов (CTO). Оцени проект и верни СТРОГО валидный JSON:
    {
      "success_probability": 75,
      "optimistic_scenario": "Кратко...",
      "pessimistic_scenario": "Кратко...",
      "optimal_scenario": "Кратко...",
      "risks": "Главные риски",
      "risk_mitigation": "Как их избежать",
      "analogs": "Конкретные примеры аналогов с названиями компаний, проектов или научных разработок (например: 'Tesla 4680 battery cells, Panasonic NCA-2170, CATL Qilin battery, проект Solid Power по твердотельным аккумуляторам')",
      "resources_needed": "Что реально потребуется для выполнения",
      "business_roi": 3.2,
      "business_cost": 150000,
      "business_payback": 14,
      "checklist": [
          {"id": 1, "task": "Закупка сырья", "done": false},
          {"id": 2, "task": "Синтез образца", "done": false},
          {"id": 3, "task": "Тестирование KPI", "done": false}
      ]
    }
    
    В поле 'analogs' ОБЯЗАТЕЛЬНО укажи 3-5 конкретных примеров с названиями реальных компаний, проектов или научных разработок. 
    Например: 'Tesla 4680 battery cells, Panasonic NCA-2170, CATL Qilin battery, проект Solid Power по твердотельным аккумуляторам, разработка Samsung SDI по литий-ионным батареям с кремниевым анодом'."""

    user_prompt = f"""
    Проект: {project_name}
    Объект исследования: {object_name}
    Гипотеза: {hypothesis_desc}
    Имеющиеся у нас ресурсы: {resources}
    """
    return ask_yandex_gpt_json(system_prompt, user_prompt, temperature=0.3)

def generate_top_recommendation(context: str) -> Dict[str, str]:
    """Генерирует топ-1 стратегическую рекомендацию на основе контекста."""
    system_prompt = """Ты — директор по инновациям. Предложи ОДНУ самую прорывную, ЕЩЕ НЕ ИЗУЧЕННУЮ гипотезу для исследований (R&D).
    Если база пуста, предложи передовую идею из материаловедения, химии или энергетики.
    Твоя рекомендация НЕ ДОЛЖНА совпадать ни с одной из существующих гипотез.
    Верни JSON:
    {"title": "Название", "description": "Суть", "target_object": "Объект", "expected_roi": "число", "evidence": "Обоснование со ссылкой на источник"}"""
    return ask_yandex_gpt_json(system_prompt, f"Текущая ситуация:\n{context}", temperature=0.5)

def generate_object_recommendation(object_name: str, metrics: str, bottlenecks: str) -> str:
    """Генерирует быструю рекомендацию для конкретного объекта."""
    system_prompt = "Ты научный консультант. Дай 1 конкретную, передовую гипотезу (текстом на 2-3 предложения), как можно улучшить этот объект и устранить его узкие места. В ответе укажи ссылку на источник (DOI, URL или название статьи/патента), подтверждающую это направление."
    user_prompt = f"Объект: {object_name}\nПоказатели: {metrics}\nПроблемы: {bottlenecks}"
    return ask_yandex_gpt(system_prompt, user_prompt, temperature=0.5)