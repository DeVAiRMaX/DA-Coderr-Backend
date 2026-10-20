from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """6 offers per page, same as PAGE_SIZE in the frontend config."""

    page_size = 6
    page_size_query_param = 'page_size'
