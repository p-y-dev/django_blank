from rest_framework import permissions
from typing import List, Optional
from user.models import UserGroup


def user_group_permission(user_group: Optional[List[UserGroup]]):
    """
    :param user_group: Список групп пользователей, для разрешения участвовать в
    запросе всем пользователям нужно передать пустой список
    """

    class Permission(permissions.BasePermission):
        def has_permission(self, request, view):
            if request.user.is_anonymous:
                return False

            if user_group in [[], None]:
                return True

            return request.user.groups.filter(name__in=user_group).exists()

    return Permission
