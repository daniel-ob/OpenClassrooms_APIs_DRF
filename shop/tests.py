from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse_lazy, reverse
from rest_framework import status
from rest_framework.test import APITestCase

from shop.models import Category, Product
from shop.mocks import mock_openfoodfact_success, ECOSCORE_GRADE


class ShopAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Fruits', active=True)
        Category.objects.create(name='Légumes', active=False)

        cls.product = cls.category.products.create(name='Ananas', active=True)
        cls.category.products.create(name='Banane', active=False)

        cls.category_2 = Category.objects.create(name='Légumes', active=True)
        cls.product_2 = cls.category_2.products.create(name='Tomate', active=True)

        cls.admin = User.objects.create(
            username="admin", is_staff=True, is_superuser=True
        )
        cls.contractor = User.objects.create(
            username="contractor", is_staff=True, is_superuser=False
        )

    def format_datetime(self, value):
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def get_article_list_data(self, articles):
        return [
            {
                'id': article.pk,
                'name': article.name,
                'date_created': self.format_datetime(article.date_created),
                'date_updated': self.format_datetime(article.date_updated),
                'product': article.product_id
            } for article in articles
        ]

    def get_product_list_data(self, products):
        return [
            {
                'id': product.pk,
                'name': product.name,
                'date_created': self.format_datetime(product.date_created),
                'date_updated': self.format_datetime(product.date_updated),
                'category': product.category_id,
                'ecoscore': ECOSCORE_GRADE
            } for product in products
        ]

    def get_category_list_data(self, categories):
        return [
            {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'date_created': self.format_datetime(category.date_created),
                'date_updated': self.format_datetime(category.date_updated),
            } for category in categories
        ]


class TestCategory(ShopAPITestCase):

    url = reverse_lazy('category-list')

    def test_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], self.get_category_list_data([self.category, self.category_2]))

    def test_create(self):
        category_count = Category.objects.count()
        response = self.client.post(self.url, data={'name': 'Nouvelle catégorie'})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Category.objects.count(), category_count)


class TestProduct(ShopAPITestCase):

    url = reverse_lazy('product-list')

    @mock.patch('shop.models.Product.call_external_api', mock_openfoodfact_success)
    def test_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_product_list_data([self.product, self.product_2]), response.json()['results'])

    @mock.patch('shop.models.Product.call_external_api', mock_openfoodfact_success)
    def test_list_filter(self):
        response = self.client.get(self.url + '?category_id=%i' % self.category.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_product_list_data([self.product]), response.json()['results'])

    def test_create(self):
        product_count = Product.objects.count()
        response = self.client.post(self.url, data={'name': 'Nouvelle catégorie'})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Product.objects.count(), product_count)

    def test_delete(self):
        response = self.client.delete(reverse('product-detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 405)
        self.product.refresh_from_db()


class TestAdminCategory(ShopAPITestCase):
    url = reverse_lazy("admin-category-list")

    def test_admin_can_create(self):
        initial_categories_count = Category.objects.count()

        self.client.force_authenticate(self.admin)
        response = self.client.post(
            self.url,
            data={"name": "New category", "description": "New category description"},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), initial_categories_count + 1)

    def test_contractor_cannot_create(self):
        initial_categories_count = Category.objects.count()

        self.client.force_authenticate(self.contractor)
        response = self.client.post(
            self.url,
            data={"name": "New category", "description": "New category description"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Category.objects.count(), initial_categories_count)

    def test_contractor_can_update(self):
        self.client.force_authenticate(self.contractor)
        response = self.client.put(
            reverse("admin-category-detail", kwargs={"pk": self.category.id}),
            data={"name": "New category", "description": "New category description"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "New category")
