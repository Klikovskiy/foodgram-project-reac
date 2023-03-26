from django.contrib.admin import ModelAdmin, TabularInline, register
from django.utils.safestring import mark_safe

from .forms import TagForm
from .models import Ingredient, IngredientAmount, Recipe, Tag

EMPTY_PLACEHOLDER = 'Нет данных'


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = EMPTY_PLACEHOLDER
    save_on_top = True


@register(IngredientAmount)
class IngredientAmountAdmin(ModelAdmin):
    pass


class IngredientInline(TabularInline):
    model = IngredientAmount
    extra = 0
    min_num = 1


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'author', 'get_image',
                    'get_count_added_to_favorite', 'get_ingredients')
    fields = (('image',), ('name', 'author'),
              ('tags', 'cooking_time'), ('text',))
    list_filter = ('name', 'author__username', 'tags')
    search_fields = ('name', 'author')
    save_on_top = True
    empty_value_display = EMPTY_PLACEHOLDER
    inlines = (IngredientInline,)

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="35"')

    def get_count_added_to_favorite(self, obj):
        return obj.favorite.count()

    def get_ingredients(self, obj):
        return ', '.join(obj.ingredients.all().values_list('name', flat=True))

    get_count_added_to_favorite.short_description = 'Добавлено в избранное'
    get_image.short_description = 'Изображение'
    get_ingredients.short_description = 'Ингридиенты'


@register(Tag)
class TagAdmin(ModelAdmin):
    form = TagForm
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = ((None, {'fields': (('name', 'slug'), 'color')}),)
    search_fields = ('name',)
    save_on_top = True
    empty_value_display = EMPTY_PLACEHOLDER
