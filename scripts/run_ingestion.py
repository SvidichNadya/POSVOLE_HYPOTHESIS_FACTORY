#!/usr/bin/env python
"""
Скрипт для загрузки и ингеста научных статей/патентов в базу знаний с обновлением графа.
Запуск: python scripts/run_ingestion.py [--doi DOI] [--file FILE]
Использует YandexGPT для извлечения графа знаний.
"""

import os
import sys
import json
import logging
import argparse
import requests

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rd_engine.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.knowledge.ingestion import ingest_document_with_ai

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Конфигурация API ---
CROSSREF_API = "https://api.crossref.org/works/"


def fetch_metadata_by_doi(doi):
    """Получение метаданных статьи по DOI через Crossref API."""
    url = CROSSREF_API + doi
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'ok' and 'message' in data:
            msg = data['message']
            title = msg.get('title', [''])[0]
            abstract = msg.get('abstract', '')
            if abstract:
                import re
                abstract = re.sub(r'<[^>]+>', ' ', abstract).strip()
            authors = [a.get('family', '') for a in msg.get('author', [])]
            meta = f"{', '.join(authors)}. {msg.get('published-print', {}).get('date-parts', [[2025]])[0][0]}"
            return {
                'title': title,
                'abstract': abstract,
                'meta': meta,
                'tags': [subj.get('name', '') for subj in msg.get('subject', [])[:5]]
            }
        else:
            logger.error(f"Ошибка API Crossref: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к Crossref: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Ингест научных документов с AI-извлечением графа')
    parser.add_argument('--doi', help='DOI статьи для загрузки через Crossref')
    parser.add_argument('--file', help='Путь к JSON-файлу с данными документа')
    parser.add_argument('--type', default='paper', choices=['paper', 'patent', 'report', 'dataset'], help='Тип документа')
    parser.add_argument('--all', action='store_true', help='Загрузить несколько примеров из списка')
    args = parser.parse_args()

    if args.doi:
        logger.info(f"Загрузка по DOI: {args.doi}")
        data = fetch_metadata_by_doi(args.doi)
        if data:
            doc = ingest_document_with_ai(data, args.type)
            logger.info(f"Документ обработан: ID={doc.id}, статус={doc.status}")
        else:
            logger.error("Не удалось загрузить данные по DOI")

    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            doc = ingest_document_with_ai(data, args.type)
            logger.info(f"Документ из файла обработан: ID={doc.id}")
        except Exception as e:
            logger.error(f"Ошибка чтения файла: {e}")

    elif args.all:
        doi_list = [
            '10.1016/j.matlet.2024.1352',
            '10.1016/j.jpowsour.2025.12345',
            '10.1016/j.compscitech.2024.12345'
        ]
        for doi in doi_list:
            logger.info(f"Загрузка {doi}...")
            data = fetch_metadata_by_doi(doi)
            if data:
                doc = ingest_document_with_ai(data, args.type)
                logger.info(f"Обработан: {doc.title[:50]}...")
            else:
                logger.warning(f"Пропускаем {doi}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()