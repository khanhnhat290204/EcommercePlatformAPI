from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import ForeignKey, OneToOneField, CharField


# Create your models here.
class User(AbstractUser):
    is_shop_owner = models.BooleanField(default=0)
    avatar = CloudinaryField(null=True)
    phone = models.CharField(max_length=10, null=True)
    is_approved = models.BooleanField(default=True)


class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# class ClassifyType(BaseModel):
#     name=models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name
#
# class ClassifyOption:
#     classify_type=models.ForeignKey(ClassifyType,on_delete=models.CASCADE)
#     value=models.CharField(max_length=50)

# class OptionType(BaseModel):
#     name = models.CharField(max_length=50)  # 'size', 'color'
#
#     def __str__(self):
#         return self.name

# class OptionValue(BaseModel):
#     option_type = models.ForeignKey(OptionType, on_delete=models.CASCADE, related_name='values')
#     value = models.CharField(max_length=50)  # 'M', 'L', 'red'
#
#     def __str__(self):
#         return f"{self.option_type.name}:{self.value}"

# class ProductVariant(BaseModel):
#     product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
#     color=models.CharField(max_length=50,default="none")
#     size=models.CharField(max_length=50,default="only-one")
#     sku = models.CharField(max_length=64, unique=True)
#     quantity = models.IntegerField(default=0)
#     fingerprint = models.CharField(max_length=255, null=True, blank=True, db_index=True)
#     # optional: price override, images...
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['product', 'fingerprint'], name='ux_product_variant_fingerprint')
#         ]
#
#     def __str__(self):
#         return f"{self.sku} ({self.quantity})"

# class VariantOptionValue(models.Model):
#     variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='variant_values')
#     option_value = models.ForeignKey(OptionValue, on_delete=models.CASCADE)
#
#     class Meta:
#         unique_together = ('variant', 'option_value')




class Inventory(BaseModel):
    quantity = models.IntegerField(default=1)
    size=models.CharField(max_length=10,default="none")
    color = models.CharField(max_length=50, default="none")
    sku=models.CharField(max_length=100,default="")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, related_name="inventory")
    # def __str__(self):
    #     return self.quantity

# class Discount(BaseModel):
#     name = models.CharField(max_length=50)
#     percentage = models.FloatField(default=0)
#     amount = models.IntegerField(default=0)
#     product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True, related_name="discounts")
#     order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True, related_name="discounts")
#
#     def __str__(self):
#         return self.name


class ProductImage(BaseModel):
    image = CloudinaryField(null=True, blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="images")


class Shop(BaseModel):
    name = models.CharField(max_length=200)
    avatar=CloudinaryField(null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address=models.CharField(max_length=200,null=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=100)
    price = models.IntegerField(default=0)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="products")

    def __str__(self):
        return self.name


class Cart(BaseModel):
    total = models.IntegerField(default=0)  # Tổng giá trị giỏ hàng hiện tại (chưa áp dụng giảm giá, phí ship)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")


class CartDetail(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_details")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="details")
    size=models.CharField(max_length=100,default="")
    color=models.CharField(max_length=100,default="")
    quantity = models.IntegerField()


class Comment(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    star = models.IntegerField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    image = CloudinaryField(null=True, blank=True)
    comment_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies")

    def __str__(self):
        return self.content

ORDER_STATUSES = [
    ('PENDING', 'Chờ xác nhận'),
    ('PAID', 'Đã thanh toán'),
    ('CANCELLED', 'Đã hủy'),
]


class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.IntegerField(default=0)  # Tổng giá trị đơn hàng cuối cùng (đã tính giảm giá, phí ship)
    shipping_address = models.CharField(max_length=150, null=True)
    phone = models.CharField(max_length=10, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUSES, default='PENDING')

    def __str__(self):
        return f"Order's {self.user.username}"

class ShopOrder(BaseModel):
    shop=models.ForeignKey(Shop,on_delete=models.CASCADE)
    shipping_fee=models.IntegerField(default=0)
    total=models.IntegerField()
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name="shop_orders")



class ShopOrderDetail(BaseModel):
    shop_order = models.ForeignKey(ShopOrder, on_delete=models.CASCADE, related_name="orderdetails")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orderdetails")
    quantity = models.IntegerField(default=0)
    inventory=models.ForeignKey(Inventory,on_delete=models.CASCADE, related_name="orderdetails",null=True)


PAYMENT_METHODS = [
    ('PAYPAL', 'Paypal'),
    ('COD', 'Thanh toán khi nhận hàng'),
]


class Payment(BaseModel):
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='COD')
    total = models.IntegerField(default=0)
    status = models.BooleanField()
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', null=True)


class CommentLike(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="liked_comments")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"