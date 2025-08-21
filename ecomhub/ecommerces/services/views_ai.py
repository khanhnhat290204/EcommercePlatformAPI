

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .gemini_service import ask_gemini
from ..models import Product
from ..serializers import ProductSerializer


# bạn đã viết sẵn
# nếu chưa có thì tạm viết hàm giả lập trả lời AI

class AIChatView(APIView):
    def post(self, request):
        user_message = request.data.get("message", "")
        product_id = request.data.get("product_id", None)
        shop=request.data.get("shop",None)
        products=Product.objects.filter(shop_id=shop)
        print(ProductSerializer(products, many=True).data)



        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        product_data = None
        if product_id:
            product=Product.objects.get(pk=product_id)
            product_data = ProductSerializer(product).data
        if shop:
            products = Product.objects.filter(shop_id=shop)
            shop_products=ProductSerializer(products, many=True).data
        reply = ask_gemini(user_message, product_data,shop_products)
        return Response({"reply": reply}, status=status.HTTP_200_OK)
