from django.db.models import F, Sum
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import (HTTP_401_UNAUTHORIZED,
                                   HTTP_201_CREATED, HTTP_200_OK,
                                   HTTP_204_NO_CONTENT)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import PageLimitPagination
from api.permissions import AuthorOrAdminOrReadOnly
from api.serializers import (IngredientSerializer, TagSerializer,
                             ShoppingCartSerializer,
                             FavoriteSerializer, UserSerializer,
                             RecipeSerializer, GetRecipeSerializer,
                             SubscribeSerializer,
                             FollowSerializer)
from api.utils import prepare_file
from recipe.models import (Ingredient, IngredientAmount, Recipe,
                           Tag, Favorites, Carts)
from users.models import User, Subscriptions


class UserViewSet(DjoserUserViewSet):
    pagination_class = PageLimitPagination

    @action(methods=('POST', 'DELETE'), detail=True)
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'author': author.id,
        }
        if request.method == 'POST':
            serializer = FollowSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=HTTP_201_CREATED
            )
        get_object_or_404(
            Subscriptions,
            user=request.user,
            author=author
        ).delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=False)
    def subscriptions(self, request):
        return self.get_paginated_response(
            SubscribeSerializer(
                self.paginate_queryset(
                    Subscriptions.objects.filter(user=request.user)
                ),
                many=True,
                context={'request': request}
            ).data
        )

    @action(methods=('GET',), detail=False)
    def me(self, request):
        if request.user.is_anonymous:
            return Response(status=HTTP_401_UNAUTHORIZED)
        return Response(
            UserSerializer(request.user).data,
            status=HTTP_200_OK
        )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.select_related('author')
    permission_classes = (AuthorOrAdminOrReadOnly,)
    pagination_class = PageLimitPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return GetRecipeSerializer
        return RecipeSerializer

    @staticmethod
    def create_object(serializers, user, recipe):
        data = {
            'user': user.id,
            'recipe': recipe.id,
        }
        serializer = serializers(
            data=data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=HTTP_201_CREATED
        )

    @staticmethod
    def delete_object(request, pk, model):
        get_object_or_404(
            model,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(methods=('POST',), detail=True)
    def favorite(self, request, pk):
        return self.create_object(
            FavoriteSerializer,
            request.user,
            get_object_or_404(Recipe, id=pk)
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_object(
            request=request,
            pk=pk,
            model=Favorites
        )

    @action(methods=('POST',), detail=True)
    def shopping_cart(self, request, pk):
        return self.create_object(
            ShoppingCartSerializer,
            request.user,
            get_object_or_404(Recipe, id=pk)
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_object(
            request=request,
            pk=pk,
            model=Carts
        )

    @action(methods=('GET',), detail=False)
    def download_shopping_cart(self, request):
        user = self.request.user
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=user).values(
            ingredient=F('ingredients__name'),
            measure=F('ingredients__measurement_unit')).order_by(
            'ingredient').annotate(sum_amount=Sum('amount'))
        return prepare_file(user, ingredients)
