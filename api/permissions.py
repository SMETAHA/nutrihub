from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            if hasattr(obj, 'created_by') and obj.created_by_id:
                return bool(getattr(obj, 'is_public', False)) or obj.created_by == request.user
            return True
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user or request.user.is_staff
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return request.user.is_staff
