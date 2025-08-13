from rest_framework import permissions


class IsOwnerShop(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view,obj) and request.user == obj.user and request.user.is_shop_owner == True and request.user.is_approved==True


class OwnerPerms(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj


class CommentOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj.user


class OrderOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.user == request.user
