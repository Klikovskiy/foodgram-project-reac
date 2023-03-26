import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipe.models import Ingredient


class Command(BaseCommand):
    help = 'Добавляет данные ингредиентов из файла json или csv'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='ingredients.csv', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        try:
            with open(os.path.join(
                    settings.BASE_DIR,
                    'data',
                    options['filename']),
                    'r',
                    encoding='utf-8') as f:
                data = csv.reader(f)
                for row in data:
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
        except FileNotFoundError:
            raise CommandError('Необходим файл ingredients в папке data')
