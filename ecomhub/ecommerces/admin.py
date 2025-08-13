from django.contrib import admin
from django.db.models import Sum

from .models import Product, ProductImage, Shop, Inventory, Cart, CartDetail, Order,  Payment, Category, Comment, CommentLike


# Register your models here.

class ProductInline(admin.TabularInline):
    model = Product
    extra = 0


class ShopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user']
    inlines = [ProductInline, ]


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ['image']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'shop']
    search_fields = ['name', 'price']
    list_filter = ['price']
    inlines = [ProductImageInline, ]


# class InventoryAdmin(admin.ModelAdmin):
#     list_display = ['quantity', 'product']
#     list_filter = ['quantity']


class CartDetailInline(admin.TabularInline):
    model = CartDetail


class CartAdmin(admin.ModelAdmin):
    list_display = ['total', 'user']
    inlines = [CartDetailInline, ]


# class OrderDetailInline(admin.TabularInline):
#     model = OrderDetail


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['user', 'total', 'shipping_address']
#     inlines = [OrderDetailInline, PaymentInline]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_method', 'total', 'status']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'star', 'content', 'image', 'comment_parent']


class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment']


admin.site.register(Shop, ShopAdmin)
admin.site.register(Product, ProductAdmin)
# admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Cart, CartAdmin)
# admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentLike, CommentLikeAdmin)
admin.site.site_header = "EcomSale Admin"