# permissions.py
from rest_framework.permissions import BasePermission

class IsSelf(BasePermission):
    """
    仅允许用户修改或查看自己的信息。
    - 对对象操作时，obj 必须是当前用户
    """
    def has_permission(self, request, view):
        # 登录用户才能访问
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 只有当前用户才能操作自己的对象
        return obj == request.user
