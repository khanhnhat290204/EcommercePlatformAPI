from django.urls import path, include, re_path
from . import views
from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .services.views_ai import AIChatView

router = routers.DefaultRouter()
router.register('categorys', views.CategoryViewSet)
router.register('users', views.UserViewSet)
router.register('shops', views.ShopViewSet)
router.register('products', views.ProductViewSet)
router.register('comments', views.CommentViewSet)
router.register('orders', views.OrderViewSet)
router.register(r'payments', views.PaymentViewSet, basename='payments')
router.register('carts', views.CartViewSet)
# router.register('shoporder',views.ShopOrder)

schema_view = get_schema_view(
    openapi.Info(
        title="EcomSale API",
        default_version='v1',
        description="APIs for EcomSaleApp",
        contact=openapi.Contact(email="khanhnhat2902@gmail.com"),
        license=openapi.License(name="Khanh Nhat@2025"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include(router.urls)),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    re_path(r'^swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'),
    re_path(r'^redoc/$',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('shop/stats/', views.ShopRevenueStatsAPIView.as_view(), name='shop-revenue-stats'),
    path("api/ai-chat/", AIChatView.as_view(), name="ai-chat"),
    # path('adminshop/stats/',views.AdminShopStatsView.as_view(),name='adminshop-revenue-stats'),
    path('paypal-success/', views.paypal_success_view, name='paypal-success'),
    path('paypal-cancel/', views.paypal_cancel_view, name='paypal-cancel'),
]
