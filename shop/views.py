from rest_framework.viewsets import ReadOnlyModelViewSet

from shop.models import Category, Product
from shop.serializers import CategorySerializer, ProductSerializer


class CategoryViewset(ReadOnlyModelViewSet):

    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.all()


class ProductViewSet(ReadOnlyModelViewSet):

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
