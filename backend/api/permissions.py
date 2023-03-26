from rest_framework import permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class AuthorOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    message = 'Редактирование доступно только автору или администратору'

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user == obj)
