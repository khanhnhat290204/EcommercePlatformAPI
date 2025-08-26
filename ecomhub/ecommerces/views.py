from _ast import Or
from collections import defaultdict
from itertools import product
from pickle import FALSE

import requests
import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
from django.template.defaulttags import comment
from django.utils.timezone import activate
from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.templatetags.rest_framework import data, items
from unicodedata import category
from urllib3 import request
from . import paginators
from . import perms
from . import serializers
from .models import Category, Product, Inventory, ProductImage, Shop, Cart, CartDetail, Comment, Order, \
    Payment, User, CommentLike, ShopOrder, ShopOrderDetail
from rest_framework import viewsets, permissions, generics, parsers, status
from rest_framework.decorators import action
from .serializers import CategorySerializer, UserSerializer, ShopSerializer, ProductSerializer, CommentSerializer, \
    ProductImageSerializer, OrderSerializer, \
    PaymentSerializer, CartSerializer, CartDetailSerializer, ShopOrderSerializer, InventorySerializer, \
    ShopOrderDetailSerializer
from django.db.models import Sum, F, functions as db_func, Q,ExpressionWrapper, FloatField
from rest_framework.views import APIView
from django.conf import settings
from datetime import datetime
from django.db.models.functions import ExtractMonth


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.filter(active=True)
    serializer_class = CategorySerializer


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView,generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [parsers.MultiPartParser, ]

    @action(methods=['get', 'patch'], url_path='current-user', detail=False)
    def get_current_user(self, request):
        if request.method.__eq__("PATCH"):
            u = request.user

            for k, v in request.data.items():
                if k in ['first_name', 'last_name', 'avatar', 'is_shop_owner', 'phone']:
                    setattr(u, k, v)
                elif k.__eq__('password'):
                    u.set_password(v)

            u.save()
            return Response(serializers.UserSerializer(u).data)

        return Response(serializers.UserSerializer(request.user).data)

    @action(methods=['get'], url_path='unapproved-user', detail=False,permission_classes=[permissions.IsAdminUser])
    def get_unapproved_user(self,request):
        users=User.objects.filter(is_approved=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @action(methods=['patch'], url_path='approved-user', detail=False,permission_classes=[permissions.IsAdminUser],parser_classes=[parsers.JSONParser])
    def aprroved_user(self,request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response({"error": "Thiếu danh sách user_ids."}, status=400)

        users = User.objects.filter(id__in=user_ids, is_approved=False)
        updated_count = users.update(is_approved=True)

        return Response(
            {"message": f"Đã duyệt {updated_count} người dùng."},
            status=status.HTTP_200_OK
        )

class ShopViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveAPIView):
    queryset = Shop.objects.filter(active=True)
    serializer_class = ShopSerializer
    # permission_classes = [perms.IsOwnerShop]
    parser_classes = [parsers.MultiPartParser, ]

    @action(methods=['get'], detail=False, url_path='my_shop', permission_classes=[perms.IsOwnerShop])
    def get_my_shop(self, request):
        try:
            shop = Shop.objects.get(user=request.user)
            serializer = ShopSerializer(shop)
        except Shop.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.data)

    @action(methods=['get'], url_path='products', detail=True)
    def get_product(self, request, pk):
        shop = self.get_object()

        products = shop.products.all()

        paginator = paginators.ProductPaginator()
        page = paginator.paginate_queryset(products, request)

        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    # @action(methods=['post'], url_path='create_product', detail=True)
    # def create_product(self, request, pk):
    #
    #     shop = Shop.objects.get(pk=pk)
    #     category = Category.objects.get(pk=request.data.get('category'))
    #     size=request.data.get('size')
    #     color=request.data.get('color')
    #     quantity=request.data.get('quantity')
    #
    #     p = ProductSerializer(data={
    #         'name': request.data.get('name'),
    #         'price': request.data.get('price'),
    #         'shop': shop.id,
    #         'category': category.id,
    #     })
    #     p.is_valid(raise_exception=True)
    #     d = p.save()
    #     print(d.id)
    #     print(request.data.get('images'))
    #     for img in request.FILES.getlist('images'):
    #         i = ProductImageSerializer(data={
    #             'product': d.id,
    #             'image': img
    #         })
    #         print(i)
    #         i.is_valid(raise_exception=True)
    #         i.save()
    #     print(d.shop)
    #     d.refresh_from_db()
    #     for s,c,q in zip(size, color, quantity):
    #         inventory = InventorySerializer(data={
    #             'size':s,
    #             'color':c,
    #             'quantity': q,
    #             'product':d.id
    #         })
    #         inventory.is_valid(raise_exception=True)
    #         i=inventory.save()
    #     return Response(ProductSerializer(d).data, status=status.HTTP_201_CREATED)
    @action(methods=['post'], url_path='create_product', detail=True)
    def create_product(self, request, pk):
        shop = Shop.objects.get(pk=pk)
        category = Category.objects.get(pk=request.data.get('category'))

        size = json.loads(request.data.get('size'))
        color = json.loads(request.data.get('color'))
        quantity = json.loads(request.data.get('quantity'))

        # 1. Tạo product
        p = ProductSerializer(data={
            'name': request.data.get('name'),
            'price': request.data.get('price'),
            'shop': shop.id,
            'category': category.id,
        })
        p.is_valid(raise_exception=True)
        product = p.save()
        print(product.id)

        # 2. Tạo inventory cho từng biến thể
        for s, c, q in zip(size, color, quantity):
            inventory = InventorySerializer(data={
                'size': s,
                'color': c,
                'quantity': q,
                'product': product.id
            })
            inventory.is_valid(raise_exception=True)
            inventory.save()

        # 3. Upload ảnh
        for img in request.FILES.getlist('images'):
            img_serializer = ProductImageSerializer(data={
                'product': product.id,
                'image': img
            })
            img_serializer.is_valid(raise_exception=True)
            img_serializer.save()

        product.refresh_from_db()
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Product.objects.filter(active=True).prefetch_related('images').order_by('id').all()
    serializer_class = ProductSerializer
    pagination_class = paginators.ProductPaginator
    filter_backends = [filters.OrderingFilter, ]
    ordering_fields = ['name', 'price']

    def get_permissions(self):
        if self.action.__eq__('get_comments'):
            if self.request.method.__eq__('POST'):
                return [permissions.IsAuthenticated()]
        elif self.action.__eq__('like'):
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    def get_object(self):
        return generics.get_object_or_404(self.queryset, pk=self.kwargs.get('pk'))

    def get_queryset(self):
        query = self.queryset

        if self.action.__eq__('list'):
            name = self.request.query_params.get('name')
            if name:
                query = query.filter(name__icontains=name)

            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            if min_price:
                query = query.filter(price__gte=min_price)
            if max_price:
                query = query.filter(price__lte=max_price)

            shop_name = self.request.query_params.get('shop_name')
            if shop_name:
                query = query.filter(shop__name__icontains=shop_name)
        for backend in list(self.filter_backends):
            query = backend().filter_queryset(self.request, query, self)
        if self.action.__eq__('retrieve') :
            query = query.prefetch_related('inventory')
        return query

    @action(methods=['get', 'post'], url_path='comments', detail=True)
    def get_comments(self, request, pk):
        if request.method.__eq__('POST'):
            print(request.method)
            t = CommentSerializer(data={
                'content': request.data.get('content'),
                'user': request.user.pk,
                'product': pk,
                'star': request.data.get('star'),
                'image': request.data.get('image'),
                'comment_parent_id': request.data.get('comment_parent_id')
            })
            t.is_valid(raise_exception=True)
            c = t.save()
            return Response(CommentSerializer(c).data, status=status.HTTP_201_CREATED)
        else:
            comments = self.get_object().comment_set.select_related('user').filter(active=True)
            p = paginators.CommentPaginator()
            page = p.paginate_queryset(comments, self.request)
            if page is not None:
                serializer = CommentSerializer(page, many=True)
                return p.get_paginated_response(serializer.data)
            else:
                return Response(CommentSerializer(comments, many=True).data)


class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.filter(active=True).order_by('id')
    serializer_class = CommentSerializer
    permission_classes = [perms.CommentOwner]


class CommentViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveAPIView):
    queryset = Comment.objects.filter(active=True).order_by('id')
    serializer_class = CommentSerializer
    pagination_class = paginators.CommentPaginator

    @action(methods=['post'], url_path='reply', detail=True)
    def reply(self, request, pk):
        try:
            comment_parent = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'Parent comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        comment_child = CommentSerializer(data={
            "content": request.data.get('content'),
            "user": request.user.pk,
            'image': request.data.get('image'),
            "product": comment_parent.product.pk
        })
        comment_child.is_valid(raise_exception=True)
        r = comment_child.save(comment_parent=comment_parent, active=True)
        return Response(CommentSerializer(r).data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], url_path='replies', detail=True)
    def get_replies(self, request, pk=None):
        try:
            parent_comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        replies = Comment.objects.filter(comment_parent=parent_comment, active=True).select_related('user')

        paginator = paginators.CommentPaginator()
        page = paginator.paginate_queryset(replies, request)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = CommentSerializer(replies, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='like')
    def like(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)

        if not created:
            return Response({'message': 'You have already liked this comment.'}, status=status.HTTP_200_OK)

        return Response({'message': 'Comment liked successfully.'}, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=True, url_path='likes')
    def get_likes(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)

        like_count = comment.likes.count()
        return Response({'like_count': like_count})



class ProductImageViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView):
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductImageSerializer
    parser_classes = [parsers.MultiPartParser]


class OrderViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.CreateAPIView):
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer
    # permission_classes = [perms.OrderOwner]
    pagination_class = paginators.OrderPaginator

    def get_queryset(self):
        query = self.queryset
        user=self.request.user
        if self.action.__eq__('list'):
            query=query.filter(user=user)
            id = self.request.query_params.get('id')
            if id:
                query = query.filter(id=id)
            return query

    def get_object(self):
        return generics.get_object_or_404(self.queryset, pk=self.kwargs.get('pk'))

    def create(self, request, *args, **kwargs):
        user = request.user
        shipping_address = request.data.get("shipping_address")
        phone = request.data.get("phone")
        order_status = request.data.get("status")
        items = request.data.get('items', [])
        product_ids = []
        shop_orders = []
        inventorys = []
        if not items:
            return Response({'error': 'Danh sách sản phẩm không được để trống'}, status=status.HTTP_400_BAD_REQUEST)

        for item in items:
            product = item.get("product_id")
            size = item.get("size")
            color = item.get("color")
            try:
                inventory = Inventory.objects.get(product=product, size=size, color=color)
            except Inventory.DoesNotExist:
                return Response(
                    {"error": f"Sản phẩm không có size '{size}' và màu '{color}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

                # Kiểm tra số lượng tồn kho
            quantity = int(item.get("quantity", 1))
            if inventory.quantity < quantity:
                return Response(
                    {
                        "error": f"Sản phẩm này, size '{size}' màu '{color}' chỉ còn {inventory.quantity} sản phẩm"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            product_ids.append(item.get("product_id"))
            inventorys.append(inventory)
        products = Product.objects.filter(id__in=product_ids).select_related("shop")
        product_map = {p.id: p for p in products}

        shop_items = defaultdict(list)
        total = 0

        for item, inv in zip(items, inventorys):
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 1))
            p = product_map[product_id]

            shop_items[p.shop.id].append((p, quantity, inv))
            total += p.price * quantity
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            phone=phone,
            status=order_status,
            total=total
        )

        for shop_id, product_list in shop_items.items():
            shop = product_list[0][0].shop
            shop_order = ShopOrder.objects.create(shop=shop, order=order, total=0)

            shop_total = 0
            # print(product_list)
            for product, quantity, inv in product_list:
                ShopOrderDetail.objects.create(shop_order=shop_order, product=product, quantity=quantity, inventory=inv)
                shop_total += product.price * quantity
                # print(product.price)
                # print(quantity)
                # print("phí hóad đơn:"+str(shop_total))s
                inv.quantity -= quantity
                inv.save()

            shop_orders.append(shop_order)

            shop_order.total = shop_total
            shop_order.save()

        return Response({
            'message': 'Đặt hàng thành công',
            'order_id': order.id,
            'order': OrderSerializer(order).data,
            'shop_order': ShopOrderSerializer(shop_orders, many=True).data

        }, status=status.HTTP_201_CREATED)


    @action(methods=['delete'], detail=True, url_path='order_cancel')
    def cancel_order(self, request, pk):
        order = self.get_object()

        if order.user != request.user:
            return Response({'error': 'Bạn không có quyền truy cập đơn hàng này'}, status=status.HTTP_400_BAD_REQUEST)

        payment = order.payment
        payment.active = False
        payment.status = False

        order.active = False
        order.status = 'CANCELLED'
        order.save()
        payment.save()

        return Response({'message': 'Đơn hàng đã được hủy thành công.'}, status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=True, url_path='update_address')
    def update_address(self, request, pk):
        order = self.get_object()
        if order.user != request.user:
            return Response({'error': 'Bạn không có quyền truy cập địa chỉ đơn hàng này!'},
                            status=status.HTTP_403_FORBIDDEN)

        new_address = request.data.get('shipping_address')

        if not new_address:
            return Response({'error': 'Missing shipping_address'}, status=status.HTTP_400_BAD_REQUEST)

        order.shipping_address = new_address
        order.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


    @action(methods=['get'], detail=True, url_path='order_details')
    def get_order_details(self, request, pk):
        order = self.get_object()
        shop_order=ShopOrder.objects.filter(order=order)
        detail={}
        for so in shop_order:
            odetails=ShopOrderDetail.objects.filter(shop_order=so)
            data=ShopOrderDetailSerializer(odetails, many=True).data
            detail[so.order_id]=data
            print(detail)

        return Response(data={ order:order.id,
                               shipping_address:order.shipping_address,
                               total:order.total,
                               detail:detail
                                     }
                        , status=status.HTTP_200_OK)

class ShopOrderViewSet(viewsets.ViewSet,generics.ListAPIView,generics.RetrieveAPIView):
    queryset = ShopOrder.objects.filter(active=True)
    serializer_class = ShopOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query=self.queryset
        user=self.request.user

        if self.action.__eq__('list'):
            if user:
                shop = Shop.objects.filter(user=user)
                query=query.filter(shop__in=shop)
        return query

    @action(methods=['get'], detail=True, url_path='detail')
    def get_order_details(self, request, pk):
        order = (Order.objects
                 .prefetch_related('shop_orders__details')  
                 .get(pk=pk))

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView):
    queryset = Payment.objects.filter(active=True)
    serializer_class = PaymentSerializer
    pagination_class = paginators.PaymentPaginator
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.queryset
        if self.action.__eq__('list'):
            id = self.request.query_params.get('id')
            if id:
                query = query.filter(id=id)
        return query

    def get_object(self):
        return generics.get_object_or_404(self.queryset, pk=self.kwargs.get('pk'))

    @action(methods=['post'], detail=True, url_path='create_paypal_payment')
    def create_paypal_payment(self, request, pk):
        if request.method == "POST":
            payment = self.get_object()
            order = payment.order

            if not order or not order.active:
                return Response({"error": "Đơn hàng không tồn tại hoặc đã bị hủy!"}, status=status.HTTP_404_NOT_FOUND)

            if order.user != request.user:
                return Response({"error": "Bạn không có quyền truy cập đơn hàng này"}, status=status.HTTP_403_FORBIDDEN)

            client_id = settings.PAYPAL_CLIENT_ID
            client_secret = settings.PAYPAL_SECRET
            auth = (client_id, client_secret)
            token_res = requests.post(
                'https://api-m.sandbox.paypal.com/v1/oauth2/token',
                data={'grant_type': 'client_credentials'},
                auth=auth
            )

            if token_res.status_code != 200:
                return Response({"error": "Lỗi khi lấy access token từ Paypal"}, status=500)
            access_token = token_res.json().get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            body = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": f"ORDER-{order.id}",
                        "description": "Thanh toán đơn hàng EcomSale",
                        "amount": {
                            "currency_code": "USD",
                            "value": str(order.total)
                        }
                    }
                ],
                "application_context": {
                    "return_url": "http://127.0.0.1:8000/payments/paypal-success",
                    "cancel_url": "http://127.0.0.1:8000/payments/paypal-cancel"
                }
            }
            res = requests.post(
                'https://api-m.sandbox.paypal.com/v2/checkout/orders',
                json=body,
                headers=headers
            )
            if res.status_code != 201:
                return Response({'error': 'Không thể tạo đơn PayPal'}, status=500)

            data = res.json()
            approve_url = next((link['href'] for link in data['links'] if link['rel'] == 'approve'), None)

            return Response({'paypal_approve_url': approve_url}, status=status.HTTP_200_OK)


def paypal_success_view(request):
    token = request.GET.get("token")
    payer_id = request.GET.get("PayerID")

    if not token or not payer_id:
        return HttpResponse("Thiếu thông tin token hoặc payer_id", status=400)

    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_SECRET
    auth = (client_id, client_secret)

    token_res = requests.post(
        'https://api-m.sandbox.paypal.com/v1/oauth2/token',
        data={'grant_type': 'client_credentials'},
        auth=auth
    )

    if token_res.status_code != 200:
        return HttpResponse("Lỗi lấy access token", status=500)

    access_token = token_res.json().get('access_token')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    capture_res = requests.post(
        f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{token}/capture',
        headers=headers
    )

    if capture_res.status_code != 201:
        return HttpResponse("Lỗi khi xác nhận thanh toán", status=500)

    reference_id = capture_res.json()['purchase_units'][0]['reference_id']
    order_id = reference_id.replace("ORDER-", "")

    try:
        payment = Payment.objects.get(order__id=order_id)
        payment.status = True
        payment.save()

        order = payment.order
        order.status = 'PAID'
        order.save()
    except Payment.DoesNotExist:
        return HttpResponse("Không tìm thấy thanh toán", status=404)

    return HttpResponse("Thanh toán thành công! Cảm ơn bạn.")


def paypal_cancel_view(request):
    token = request.GET.get("token")
    if not token:
        return HttpResponse("Mã đơn hàng không có trong yêu cầu!", status=400)

    return HttpResponse("Thanh toán đã bị hủy bỏ! Bạn có thể thử lại và chọn phương thức khác", status=200)


class CartViewSet(viewsets.GenericViewSet):
    queryset = Cart.objects.filter(active=True).prefetch_related('details')
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_user_cart(self):
        cart, created = Cart.objects.get_or_create(
            user=self.request.user
        )
        return cart

    @action(methods=['get'], detail=False, url_path='my_cart')
    def my_cart(self, request):
        cart = self.get_user_cart()

        cart.total = sum([d.product.price * d.quantity for d in cart.details.all()])
        cart.save(update_fields=['total'])

        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='add_product')
    def add_product(self, request):
        cart = self.get_user_cart()
        product_id = request.data.get('product_id')
        size=request.data.get('size')
        color=request.data.get('color')
        stock=0
        inventory=Inventory.objects.filter(product=product_id)
        if size is not None:
            inventory=inventory.filter(size=size)
        if color is not None:
            inventory=inventory.filter(color=color)

        for i in inventory:
            stock+=i.quantity
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'error': f'Sản phẩm với ID {product_id} không tồn tại.'})
        print(product)
        try:
            quantity = int(request.data.get('quantity', 1))
            print(stock)
            if(stock < quantity):
                return Response({'error': f'Sản phẩm không đủ số lượng'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Số lượng không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
            


        if not product_id:
            return Response({'error': 'Vui lòng cung cấp ID sản phẩm.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            return Response({'error': 'Số lượng sản phẩm phải lớn hơn 0.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_detail, created = CartDetail.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            color=color,
            defaults={'quantity': quantity
                      }
        )

        if not created:
            cart_detail.quantity = F('quantity') + quantity
            cart_detail.save(update_fields=['quantity'])
            cart_detail.refresh_from_db()

        cart.total = sum([d.product.price * d.quantity for d in cart.details.all()])
        cart.save(update_fields=['total'])

        return Response(
            CartDetailSerializer(cart_detail).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(methods=['delete'], detail=False, url_path='remove_product')
    def remove_product(self, request):
        cart = self.get_user_cart()
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({'error': 'Vui lòng cung cấp ID sản phẩm.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_detail = CartDetail.objects.filter(cart=cart, product__id=product_id)
            cart_detail.delete()
        except CartDetail.DoesNotExist:
            return Response({'error': 'Sản phẩm không tồn tại trong giỏ hàng.'}, status=status.HTTP_404_NOT_FOUND)

        cart.total = sum([d.product.price * d.quantity for d in cart.details.all()])
        cart.save(update_fields=['total'])

        return Response({'message': 'Đã xoá sản phẩm khỏi giỏ hàng.'}, status=status.HTTP_200_OK)


class ShopRevenueStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # def get(self, request):
    #     user = request.user
    #
    #     if not user.is_shop_owner:
    #         return Response({'error': 'Bạn không có quyền truy cập'}, status=status.HTTP_403_FORBIDDEN)
    #
    #     shop = getattr(user, 'shop', None)
    #
    #     if not shop:
    #         return Response({'error': 'Không tìm thấy shop'}, status=status.HTTP_404_NOT_FOUND)
    #
    #     year = int(request.query_params.get('year', datetime.now().year))
    #     month = request.query_params.get('month')
    #     quarter = request.query_params.get('quarter')
    #
    #     orderdetails = OrderDetail.objects.filter(
    #         product__shop=shop,
    #         order__status='COMPLETED',
    #         created_date__year=year
    #     )
    #
    #     if month:
    #         orderdetails = orderdetails.filter(created_date__month=int(month))
    #
    #     if quarter:
    #         quarter = int(quarter)
    #         start_month = (quarter - 1) * 3 + 1
    #         end_month = start_month + 2
    #         orderdetails = orderdetails.filter(created_date__month__gte=start_month, created_date__month__lte=end_month)
    #
    #     product_stats = orderdetails.values(name=F('product__name')).annotate(
    #         total_quantity=Sum('quantity'),
    #         total_revenue=ExpressionWrapper(F('quantity') * F('product__price'), output_field=FloatField())
    #     ).order_by('-total_revenue')
    #
    #     category_stats = orderdetails.values(name=F('product__category__name')).annotate(
    #         total_quantity=Sum('quantity'),
    #         total_revenue=Sum(F('quantity') * F('product__price'))
    #     ).order_by('-total_revenue')
    #
    #     return Response({
    #         'product_stats': product_stats,
    #         'category_stats': category_stats
    #     })

class AdminShopStatsView(viewsets.GenericViewSet):
    queryset = Product.objects.filter(active=True)
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

