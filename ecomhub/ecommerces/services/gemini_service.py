import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key="AIzaSyAsFMT_csgYT7iV_3HxTwYsVd0EGxyzT-k")
model = genai.GenerativeModel("gemini-1.5-flash")

def ask_gemini(user_message, product_data=None,shop_products=None):
    context = ""
    if product_data:
        context = f"""
            Đây là thông tin sản phẩm:
            {product_data}
            
            Đây là thông tin sản phẩm:
            {shop_products}

            Hãy tư vấn khách hàng dựa trên sản phẩm này.
            """

    prompt = f"""
        Người dùng hỏi: {user_message}

        {context}

        Lưu ý: chỉ tư vấn dựa trên dữ liệu sản phẩm đã cung cấp, không bịa ra thông tin.
        """

    response = model.generate_content(prompt)
    return response.text if response else "Xin lỗi, tôi chưa hiểu ý bạn."
