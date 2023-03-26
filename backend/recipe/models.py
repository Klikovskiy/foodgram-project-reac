from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import (CASCADE, CharField, ForeignKey,
                              ImageField, ManyToManyField, Model,
                              SlugField, TextField,
                              UniqueConstraint, PositiveSmallIntegerField)

from users.models import User


class Ingredient(Model):
    measurement_unit = CharField(verbose_name='Единицы измерения',
                                 max_length=settings.RECIPE_CHAR_FIELD_LENG, )
    name = CharField(verbose_name='Ингредиент',
                     max_length=settings.RECIPE_CHAR_FIELD_LENG, )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            UniqueConstraint(name='Unique_measure_for_ingredient',
                             fields=('name', 'measurement_unit'), ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientAmount(Model):
    amount = PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(1, 'Не может быть меньше 1.'),), )
    ingredients = ForeignKey(to=Ingredient,
                             on_delete=CASCADE,
                             related_name='ingredient_recipe',
                             verbose_name='Ингредиенты, '
                                          'связанные с рецептом', )
    recipe = ForeignKey(to='Recipe',
                        on_delete=CASCADE,
                        related_name='ingredient_recipe',
                        verbose_name='Рецепты, содержащие ингредиенты', )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ('recipe',)
        constraints = (
            UniqueConstraint(name='Unique_ingredient_in_recipe',
                             fields=('ingredients', 'recipe')),
        )

    def __str__(self):
        return f'{self.recipe}: {self.amount}, {self.ingredients}'


class Tag(Model):
    color = CharField(
        verbose_name='Код цвета',
        max_length=7,
        default='#ffffff',
        validators=[RegexValidator(regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$", )])

    name = CharField(verbose_name='Тег',
                     max_length=settings.RECIPE_CHAR_FIELD_LENG,
                     unique=True, )
    slug = SlugField(verbose_name='Slug для тега',
                     max_length=200,
                     unique=True, )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(Model):
    author = ForeignKey(to=User,
                        on_delete=CASCADE,
                        verbose_name='Автор рецепта',
                        related_name='recipes')
    cooking_time = PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(1, 'Значение не может быть менее 1 минуты.'),))
    ingredients = ManyToManyField(to=Ingredient,
                                  through=IngredientAmount,
                                  verbose_name='Список ингредиентов',
                                  related_name='recipes')
    image = ImageField(verbose_name='Изображение',
                       upload_to='recipe_images/')
    name = CharField(verbose_name='Название рецепта',
                     max_length=settings.RECIPE_CHAR_FIELD_LENG)

    tags = ManyToManyField(to=Tag,
                           related_name='recipes',
                           verbose_name='Теги')
    text = TextField(verbose_name='Описание рецепта', )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = (UniqueConstraint(name='unique_per_author',
                                        fields=('name', 'author')),)

    def __str__(self):
        return self.name


class RecipeBase(Model):
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        verbose_name='Пользователь'
    )
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class Favorites(RecipeBase):
    class Meta(RecipeBase.Meta):
        default_related_name = 'favorite'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_recipe'
            )
        ]
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class Carts(RecipeBase):
    class Meta(RecipeBase.Meta):
        default_related_name = 'shopping_cart'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shopping_cart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
