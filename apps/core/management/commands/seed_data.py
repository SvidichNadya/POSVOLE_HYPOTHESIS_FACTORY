from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.core.models import Project
from apps.objects.models import ResearchObject, Metric, Bottleneck, Strength, SliderParameter
from apps.hypotheses.models import Hypothesis, Evidence, RoadmapStep
from apps.knowledge.models import KnowledgeDocument
from apps.graph.models import GraphNode, GraphEdge

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(username='admin', defaults={'is_superuser': True, 'is_staff': True})
        user.set_password('adminpass')
        user.save()

        project, _ = Project.objects.get_or_create(name='R&D Project Alpha', defaults={'owner': user})

        obj1, _ = ResearchObject.objects.get_or_create(
            name='Литий-ионный аккумулятор (NMC-811)',
            defaults={'project': project, 'status': 'Диагностировано'}
        )
        Metric.objects.get_or_create(object=obj1, name='Плотность энергии', defaults={'current_value': '250 Wh/kg', 'target_value': '300 Wh/kg'})
        Metric.objects.get_or_create(object=obj1, name='Ресурс службы', defaults={'current_value': '5 лет', 'target_value': '7 лет'})
        Bottleneck.objects.get_or_create(object=obj1, description='Катодная деградация лимитирует срок службы на 34%.')
        Strength.objects.get_or_create(object=obj1, description='Высокий КПД (>99.1%)')
        SliderParameter.objects.get_or_create(object=obj1, name='Содержание Никеля (%)', defaults={'key': 'nickel', 'min_value': 60, 'max_value': 95, 'default_value': 81, 'step': 1, 'unit': '%'})
        SliderParameter.objects.get_or_create(object=obj1, name='Концентрация Sc', defaults={'key': 'scandium', 'min_value': 0.0, 'max_value': 1.0, 'default_value': 0.2, 'step': 0.05, 'unit': '%'})

        obj2, _ = ResearchObject.objects.get_or_create(
            name='Углеволоконный эпоксидный композит (T800)',
            defaults={'project': project, 'status': 'Сбор данных'}
        )
        Metric.objects.get_or_create(object=obj2, name='Предел прочности', defaults={'current_value': '2100 МПа', 'target_value': '2500 МПа'})
        Metric.objects.get_or_create(object=obj2, name='Трещиностойкость G_Ic', defaults={'current_value': '320 J/m²', 'target_value': '450 J/m²'})
        Bottleneck.objects.get_or_create(object=obj2, description='Хрупкость матрицы при -50°C')
        Strength.objects.get_or_create(object=obj2, description='Отличное соотношение прочности к весу')
        SliderParameter.objects.get_or_create(object=obj2, name='Объемная доля волокна', defaults={'key': 'fiber', 'min_value': 45, 'max_value': 70, 'default_value': 55, 'step': 1, 'unit': '%'})

        hypo, _ = Hypothesis.objects.get_or_create(
            title='Использование наноструктурированного катода на основе скандия',
            defaults={
                'object': obj1,
                'description': 'Внедрение шпинели LiMn2O4 с 0.2% Sc блокирует микротрещины.',
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
        Evidence.objects.get_or_create(hypothesis=hypo, text='Легирование Sc (0.2%) -> образование шпинели', defaults={'source': 'DOI: 10.1016/j.matlet.2024.1352'})
        RoadmapStep.objects.get_or_create(hypothesis=hypo, name='Фаза 1: Лабораторный синтез', defaults={'duration': '2 мес.', 'risk_level': 'Низкий', 'order': 1})

        KnowledgeDocument.objects.get_or_create(
            title='Stabilization of high-voltage NMC-811 cathodes via rare-earth doping',
            defaults={
                'doc_type': 'paper',
                'meta': 'Journal of Power Sources, 2025',
                'abstract': 'Исследование показывает, что Sc минимизирует фазовые переходы.',
                'tags': ['NMC-811', 'Scandium']
            }
        )

        node1, _ = GraphNode.objects.get_or_create(node_id='1', defaults={'label': 'Содержание Ni', 'node_type': 'param'})
        node2, _ = GraphNode.objects.get_or_create(node_id='2', defaults={'label': 'Плотность энергии', 'node_type': 'kpi'})
        node3, _ = GraphNode.objects.get_or_create(node_id='3', defaults={'label': 'Ресурс службы', 'node_type': 'kpi'})
        GraphEdge.objects.get_or_create(source=node1, target=node2, defaults={'relation_type': 'усиливает', 'color': '#135BEC'})
        GraphEdge.objects.get_or_create(source=node1, target=node3, defaults={'relation_type': 'увеличивает', 'color': '#EF4444'})

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно загружены'))