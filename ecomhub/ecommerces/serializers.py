from itertools import product

from django.template.defaulttags import comment
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer,SerializerMethodField
from unicodedata import category

from .models import Category, Product, Inventory, ProductImage, Shop, Cart, CartDetail, Comment, Order, \
    Payment, User, ShopOrder, ShopOrderDetail


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'is_shop_owner', 'avatar', 'phone','is_superuser','is_approved']

        extra_kwargs = {
            'is_superuser': {
                'read_only': True
            },
            'password': {
                'write_only': True
            }
        }



    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        if u.is_shop_owner:
            u.is_approved=False
        else:
            u.is_approved=True
        u.save()

        return u

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')

        if isinstance(avatar, str):
            instance.avatar = avatar
        elif avatar:
            instance.avatar = avatar

        instance.save()
        return instance


class ShopSerializer(ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name','user']


class ProductImageSerializer(ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image','product']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image'] = instance.image.url
        return data

class InventorySerializer(ModelSerializer):
    class Meta:
        model= Inventory
        fields=['id','quantity','size','color','product']

class ProductSerializer(ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    inventory= InventorySerializer(many=True,read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'shop', 'category', 'price', 'images','inventory']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # representation['shop'] = instance.shop.__str__()  # or instance.shop.__str__()
        representation['category'] = instance.category.__str__()

        view = self.context.get('view')
        if view and getattr(view, 'action', None) != 'retrieve':
            representation.pop('inventory', None)
        return representation



class ProductDetailSerializer(ProductSerializer):
    pass


class CommentSerializer(ModelSerializer):
    like_count = serializers.SerializerMethodField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user).data
        return data

    def get_like_count(self, obj):
        return obj.likes.count()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'star', 'content', 'image', 'comment_parent', 'product', 'like_count']

        extra_kwargs = {
            'product': {
                'write_only': True
            }
        }


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'payment_method', 'total', 'status', 'order']


class OrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'active', 'user', 'total', 'shipping_address', 'phone','status']


class ShopOrderSerializer(ModelSerializer):
    class Meta:
        model = ShopOrder
        fields=['id','shop','shipping_fee','total','order']

class ShopOrderDetailSerializer(ModelSerializer):
    class Meta:
        model=ShopOrderDetail
        fields=['id','shop_order','product','quantity','inventory']




# class OrderDetailWithProductSerializer(ModelSerializer):
#     product = ProductSerializer()
#
#     class Meta:
#         model = OrderDetail
#         fields = ['id', 'product', 'quantity']


class CartDetailSerializer(ModelSerializer):
    class Meta:
        model = CartDetail
        fields = ['id', 'quantity', 'product', 'cart','size','color']


class CartSerializer(ModelSerializer):
    details = CartDetailSerializer(many=True, read_only=True)  # Error here without read_only or source

    class Meta:
        model = Cart
        fields = ['id', 'user', 'total', 'details']
