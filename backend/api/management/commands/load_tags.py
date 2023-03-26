import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipe.models import Tag


class Command(BaseCommand):
    help = 'Добавляет данные ингредиентов из файла json или csv'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='tags.csv', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        try:
            with open(os.path.join(settings.BASE_DIR,
                                   'data', options['filename']), 'r',
                      encoding='utf-8') as f:
                data = csv.reader(f)
                for row in data:
                    name, slug, color = row
                    Tag.objects.get_or_create(color=color,
                                              name=name,
                                              slug=slug)
        except FileNotFoundError:
            raise CommandError('Необходим файл tags в папке data')
