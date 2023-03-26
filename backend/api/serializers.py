from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework.fields import ReadOnlyField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import (ModelSerializer, RegexField,
                                        SerializerMethodField,
                                        ValidationError, IntegerField)
from rest_framework.validators import UniqueTogetherValidator

from api.utils import recipe_amount_ingredients_set
from recipe.models import (Ingredient, Recipe, Tag, Favorites,
                           Carts, IngredientAmount)
from users.models import User, Subscriptions


class UserSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed',)
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and obj.following.filter(user=request.user).exists())


class FavoriteSerializer(ModelSerializer):
    class Meta:
        model = Favorites
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=['recipe', 'user'],
                message='Рецепт уже находится в избранном'
            )
        ]


class ShoppingCartSerializer(ModelSerializer):
    class Meta:
        model = Carts
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Carts.objects.all(),
                fields=['recipe', 'user'],
                message='Рецепт уже добавлен в список покупок-'
            )
        ]


class RecipeSmallSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ['__all__']


class SubscribeSerializer(ModelSerializer):
    recipes = SerializerMethodField(read_only=True)
    recipes_count = SerializerMethodField(read_only=True)
    id = ReadOnlyField(source='author.id')
    email = ReadOnlyField(source='author.email')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'recipes',
                  'recipes_count')

    def get_recipes(self, obj):
        recipes = obj.author.recipes.all()
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSmallSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class FollowSerializer(UserSerializer):
    class Meta:
        model = Subscriptions
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=('user', 'author'),
                message='Ошибка'
            )
        ]

    def to_representation(self, instance):
        return SubscribeSerializer(instance).data


class UserFollowsSerializer(UserSerializer):
    recipes = SerializerMethodField(method_name='paginated_recipes')
    recipes_count = SerializerMethodField(method_name='get_recipes_count')

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'recipes', 'recipes_count', 'is_subscribed',)
        read_only_fields = ['__all__']

    def get_recipes_count(self, obj: int) -> int:
        return obj.author.recipes.count()

    def get_is_subscribed(*args) -> bool:
        return True

    def paginated_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        context = {'request': request}
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.author.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSmallSerializer(recipes, many=True, context=context).data


class GetIngredientsRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredients.id')
    name = ReadOnlyField(source='ingredients.name')
    measurement_unit = ReadOnlyField(source='ingredients.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name',
                  'measurement_unit',
                  'amount')


class AddIngredientToRecipeSerializer(ModelSerializer):
    id = IntegerField()
    amount = IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ['__all__']
        color = RegexField(r'^#(?:[0-9a-fA-F]{1,2}){3}$')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ['__all__']


class GetRecipeSerializer(ModelSerializer):
    author = UserSerializer()
    ingredients = GetIngredientsRecipeSerializer(source='ingredient_recipe',
                                                 many=True)
    tags = TagSerializer(many=True)
    is_favorited = SerializerMethodField(method_name='get_is_favorited')
    is_in_shopping_cart = SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name',
                  'image', 'text', 'ingredients',
                  'tags', 'cooking_time',
                  'is_in_shopping_cart',
                  'is_favorited')

    def _exist(self, model, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return model.objects.filter(
            user=request.user,
            recipe__id=obj.id
        ).exists()

    def get_is_favorited(self, obj):
        return self._exist(Favorites, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._exist(Carts, obj)


class SerializerRecipeCookingTime(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('cooking_time',)


class RecipeSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = AddIngredientToRecipeSerializer(many=True,
                                                  source='ingredient_recipe', )
    is_favorited = SerializerMethodField(method_name='get_is_favorited')
    is_in_shopping_cart = SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )
    image = Base64ImageField()
    cooking_time = IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart',)
        read_only_fields = ('is_favorite', 'is_shopping_cart',)

    def get_ingredients(self, obj: object):
        return obj.ingredients.values('id', 'name', 'measurement_unit',
                                      amount=F('recipe__amount'))

    def _exist(self, model, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return model.objects.filter(user=request.user,
                                        recipe__id=obj.id).exists()

    def get_is_favorited(self, obj):
        return self._exist(Favorites, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._exist(Carts, obj)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise ValidationError(
                'Необходимо выбрать ингредиенты!')
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise ValidationError(
                    'Количество не может быть меньше 1!')

        ids = [ingredient['id'] for ingredient in ingredients]
        if len(ids) != len(set(ids)):
            raise ValidationError(
                'Данный ингредиент уже есть в рецепте!')
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise ValidationError('Необходимо выбрать теги!')
        return tags

    def validate_cooking_time(self, data):
        cooking_time = self.initial_data.get('cooking_time')
        if int(cooking_time) <= 0:
            raise ValidationError('Время приготовления должно быть больше 0!')
        return data

    def create_tags(self, recipe, tags):
        for tag in tags:
            recipe.tags.add(tag)

    def create_ingredients(self, recipe, ingredients):
        IngredientAmount.objects.bulk_create(
            [IngredientAmount(recipe=recipe,
                              ingredients=get_object_or_404(Ingredient,
                                                            pk=ingredient[
                                                                'id']),
                              amount=ingredient['amount'])
             for ingredient in ingredients])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_recipe')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.get('tags')
        ingredients = validated_data.get('ingredient')

        recipe.image = validated_data.get(
            'image', recipe.image)
        recipe.name = validated_data.get(
            'name', recipe.name)
        recipe.text = validated_data.get(
            'text', recipe.text)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            recipe_amount_ingredients_set(recipe, ingredients)

        recipe.save()
        return recipe
