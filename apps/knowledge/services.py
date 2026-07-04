import logging

logger = logging.getLogger(__name__)

def search_internet_bulk(query: str, filters: dict) -> list:
    """Массовый поиск в сети с применением фильтров пользователя."""
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        
        timelimit = 'w' if filters.get('fresh_only') else None
        
        # Если нужны только проверенные - добавляем ключевые слова к запросу
        if filters.get('verified_only'):
            query += " research paper OR peer reviewed OR scientific journal"
            
        # Точное совпадение
        if filters.get('exact_match'):
            query = f'"{query}"'
            
        logger.info(f"Запуск Web-агента с запросом: {query}")
        
        # Получаем 5 лучших источников
        results = ddgs.text(query, timelimit=timelimit, max_results=5)
        return list(results)
    except Exception as e:
        logger.error(f"DDG Search error: {e}")
        return []

def search_documents(query, doc_type=None):
    from .models import KnowledgeDocument
    qs = KnowledgeDocument.objects.all().order_by('-id')
    if doc_type and doc_type != 'all':
        qs = qs.filter(doc_type=doc_type)
    if query:
        qs = qs.filter(title__icontains=query) | qs.filter(abstract__icontains=query) | qs.filter(meta__icontains=query)
    return qs