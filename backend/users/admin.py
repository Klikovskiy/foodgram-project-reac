from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'get_recipe_count', 'get_subs_count')
    fieldsets = (
        (
            None, {
                'fields': (
                    ('username', 'email'),
                    ('first_name', 'last_name'),
                    ('date_joined',),
                    ('password',)
                ),
            }
        ),
        (
            'Права доступа', {
                'classes': ('collapse',),
                'fields': (
                    'is_active',
                    'is_superuser',
                    'is_staff'
                ),
            }
        )
    )

    def get_recipe_count(self, obj):
        return obj.recipes.count()

    def get_subs_count(self, obj):
        return obj.follower.count()

    get_recipe_count.short_description = 'Рецептов'
    get_subs_count.short_description = 'Подписчиков'

    search_fields = ('username', 'email')
    list_filter = ('username', 'first_name', 'email')
    save_on_top = True
    empty_value_display = '-пусто-'
