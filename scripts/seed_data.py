#!/usr/bin/env python
"""
Скрипт для инициализации базы данных тестовыми данными.
Запуск: python scripts/seed_data.py
Использует get_or_create для идемпотентности.
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rd_engine.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from apps.core.models import Project
from apps.objects.models import ResearchObject, Metric, Bottleneck, Strength, SliderParameter
from apps.hypotheses.models import Hypothesis, Evidence, RoadmapStep
from apps.knowledge.models import KnowledgeDocument
from apps.graph.models import GraphNode, GraphEdge

@transaction.atomic
def main():
    print("🚀 Загрузка тестовых данных...")

    # --- Пользователь ---
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'is_superuser': True, 'is_staff': True}
    )
    if created:
        user.set_password('admin')
        user.save()
        print("✅ Создан суперпользователь admin (пароль: admin)")
    else:
        print("ℹ️ Пользователь admin уже существует")

    # --- Проект ---
    project, _ = Project.objects.get_or_create(name='R&D Project Alpha', defaults={'owner': user})
    print(f"ℹ️ Проект: {project.name}")

    # --- Объект 1: Аккумулятор ---
    obj1, created = ResearchObject.objects.get_or_create(
        name='Литий-ионный аккумулятор (NMC-811)',
        defaults={
            'project': project,
            'status': 'Диагностировано',
            'description': 'Исследование катодного и анодного составов для повышения плотности энергии и ресурса'
        }
    )
    if created:
        print(f"✅ Создан объект: {obj1.name}")

    # Метрики
    metric_names = [
        ('Плотность энергии', '250 Wh/kg', '300 Wh/kg'),
        ('Ресурс службы', '5 лет', '7 лет'),
    ]
    for name, cur, tgt in metric_names:
        Metric.objects.get_or_create(object=obj1, name=name, defaults={'current_value': cur, 'target_value': tgt})

    Bottleneck.objects.get_or_create(object=obj1, description='Катодная деградация лимитирует срок службы на 34%.')
    Strength.objects.get_or_create(object=obj1, description='Высокий КПД (>99.1%)')

    sliders = [
        ('Содержание Никеля (%)', 'nickel', 60, 95, 81, 1, '%'),
        ('Концентрация Sc', 'scandium', 0.0, 1.0, 0.2, 0.05, '%'),
    ]
    for name, key, minv, maxv, default, step, unit in sliders:
        SliderParameter.objects.get_or_create(
            object=obj1, key=key,
            defaults={'name': name, 'min_value': minv, 'max_value': maxv, 'default_value': default, 'step': step, 'unit': unit}
        )

    # --- Объект 2: Композит ---
    obj2, created = ResearchObject.objects.get_or_create(
        name='Углеволоконный эпоксидный композит (T800)',
        defaults={
            'project': project,
            'status': 'Сбор данных',
            'description': 'Повышение трещиностойкости полимерной матрицы для элементов фюзеляжа'
        }
    )
    if created:
        print(f"✅ Создан объект: {obj2.name}")

    Metric.objects.get_or_create(object=obj2, name='Предел прочности', defaults={'current_value': '2100 МПа', 'target_value': '2500 МПа'})
    Metric.objects.get_or_create(object=obj2, name='Трещиностойкость G_Ic', defaults={'current_value': '320 J/m²', 'target_value': '450 J/m²'})
    Bottleneck.objects.get_or_create(object=obj2, description='Хрупкость матрицы при отрицательных температурах')
    Strength.objects.get_or_create(object=obj2, description='Отличное соотношение прочности к весу')
    SliderParameter.objects.get_or_create(
        object=obj2, key='fiber',
        defaults={'name': 'Объемная доля волокна', 'min_value': 45, 'max_value': 70, 'default_value': 55, 'step': 1, 'unit': '%'}
    )

    # --- Гипотеза ---
    hypo, created = Hypothesis.objects.get_or_create(
        title='Использование наноструктурированного катода на основе скандия',
        defaults={
            'object': obj1,
            'description': 'Внедрение ультрадисперсной шпинели LiMn₂O₄, легированной 0.2% Sc, блокирует разрастание микротрещин по границам зерен.',
            'status': 'validation',
            'novelty_score': 84,
            'feasibility_score': 0.72,
            'research_cost': 150000,
            'economic_benefit': 3000000,
            'payback_months': 8,
            'roi': 4.2,
            'complexity_data': {'sci': 8, 'tech': 6, 'res': 5, 'org': 4}
        }
    )
    if created:
        print(f"✅ Создана гипотеза: {hypo.title}")

    Evidence.objects.get_or_create(
        hypothesis=hypo,
        text='Легирование Sc (0.2%) -> образование шпинели',
        defaults={'source': 'DOI: 10.1016/j.matlet.2024.1352'}
    )
    RoadmapStep.objects.get_or_create(
        hypothesis=hypo,
        name='Фаза 1: Лабораторный синтез порошков',
        defaults={'duration': '2 мес.', 'risk_level': 'Низкий', 'order': 1}
    )

    # --- База знаний ---
    kb, created = KnowledgeDocument.objects.get_or_create(
        title='Stabilization of high-voltage NMC-811 cathodes via rare-earth doping',
        defaults={
            'doc_type': 'paper',
            'meta': 'Journal of Power Sources, 2025. Смирнов К.Д. и др.',
            'abstract': 'Исследование показывает, что введение ультрамалых концентраций скандия и лантана минимизирует структурные фазовые переходы.',
            'tags': ['NMC-811', 'Scandium', 'High Voltage']
        }
    )
    if created:
        print(f"✅ Добавлен документ: {kb.title}")

    # --- Граф ---
    nodes_data = {
        '1': ('Содержание Ni', 'param', 'Процентное содержание Ni в кристаллической решетке катода'),
        '2': ('Плотность энергии', 'kpi', 'Удельная энергоемкость ячейки, Wh/kg'),
        '3': ('Ресурс службы', 'kpi', 'Количество циклов до падения емкости'),
        '4': ('Легирование Sc (0.2%)', 'param', 'Внедрение ионов скандия в октаэдрические пустоты'),
        '5': ('Блокировка зерен', 'mech', 'Защита границ кристаллитов от диффузии'),
        '6': ('Растрескивание катода', 'fail', 'Межкристаллитное разрушение'),
    }
    for nid, (label, ntype, desc) in nodes_data.items():
        GraphNode.objects.get_or_create(node_id=nid, defaults={'label': label, 'node_type': ntype, 'description': desc})

    edges = [
        ('1', '2', 'усиливает', '#135BEC', False),
        ('1', '6', 'увеличивает', '#EF4444', False),
        ('6', '3', 'уменьшает', '#EF4444', False),
        ('4', '5', 'усиливает', '#135BEC', False),
        ('5', '6', 'блокирует', '#10B981', False),
        ('4', '2', 'белое пятно (эффект?)', '#F59E0B', True),
    ]
    for src, tgt, rel, color, dash in edges:
        s = GraphNode.objects.get(node_id=src)
        t = GraphNode.objects.get(node_id=tgt)
        GraphEdge.objects.get_or_create(source=s, target=t, defaults={'relation_type': rel, 'color': color, 'is_dashed': dash})

    print("✅ Граф заполнен узлами и рёбрами.")

    # Подсчёт итогов
    print("\n📊 Итоговые данные:")
    print(f"  - Объектов: {ResearchObject.objects.count()}")
    print(f"  - Гипотез: {Hypothesis.objects.count()}")
    print(f"  - Документов БЗ: {KnowledgeDocument.objects.count()}")
    print(f"  - Узлов графа: {GraphNode.objects.count()}")
    print(f"  - Связей графа: {GraphEdge.objects.count()}")
    print("\n✅ Загрузка тестовых данных завершена успешно!")

if __name__ == "__main__":
    main()