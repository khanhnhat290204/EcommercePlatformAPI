from rest_framework import pagination


class CoursePaginator(pagination.PageNumberPagination):
    page_size = 6


class CommentPaginator(pagination.PageNumberPagination):
    page_size = 10


class OrderPaginator(pagination.PageNumberPagination):
    page_size = 10


class ProductPaginator(pagination.PageNumberPagination):
    page_size = 3


class PaymentPaginator(pagination.PageNumberPagination):
    page_size = 10


class ProductPaginator(pagination.PageNumberPagination):
    page_size = 20
