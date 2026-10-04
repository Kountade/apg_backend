# core/pagination.py
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Pagination standard APG : 25 éléments par page, ajustable via ?page_size=N.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200
