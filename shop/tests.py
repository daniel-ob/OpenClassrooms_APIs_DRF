from django.urls import reverse_lazy, reverse
from rest_framework import status
from rest_framework.test import APITestCase

from shop.models import Category, Product


class ShopAPITestCase(APITestCase):
    @staticmethod
    def format_datetime(value):
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class TestCategory(ShopAPITestCase):
    url = reverse_lazy("category-list")

    def test_list(self):
        category = Category.objects.create(name="Fruits", active=True)
        Category.objects.create(name="Légumes", active=False)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                "id": category.id,
                "name": category.name,
                "date_created": self.format_datetime(category.date_created),
                "date_updated": self.format_datetime(category.date_updated),
            }
        ]
        self.assertEqual(response.json(), expected)

    def test_create(self):
        self.assertFalse(Category.objects.exists())
        response = self.client.post(self.url, data={"name": "Tentative"})
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Category.objects.exists())


class TestProduct(ShopAPITestCase):
    def test_list(self):
        category = Category.objects.create(name="Personal Care", active=True)
        active_product = Product.objects.create(
            name="Toothbrush", active=True, category=category
        )
        Product.objects.create(
            name="Toothpaste", active=False, category=category
        )  # inactive product must not be shown on list

        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                "id": active_product.id,
                "date_created": self.format_datetime(active_product.date_created),
                "date_updated": self.format_datetime(active_product.date_updated),
                "name": active_product.name,
                "category": category.id,
            }
        ]
        self.assertEqual(response.json(), expected)

    def test_detail(self):
        category = Category.objects.create(name="Personal Care", active=True)
        product = Product.objects.create(
            name="Toothbrush", active=True, category=category
        )

        response = self.client.get(reverse("product-detail", args=[product.id]))
        self.assertEqual(response.status_code, 200)

        expected = {
            "id": product.id,
            "date_created": self.format_datetime(product.date_created),
            "date_updated": self.format_datetime(product.date_updated),
            "name": product.name,
            "category": category.id,
        }
        self.assertEqual(response.json(), expected)

    def test_list_filter_by_category(self):
        category = Category.objects.create(name="Personal Care", active=True)
        product = Product.objects.create(
            name="Toothbrush", active=True, category=category
        )
        Product.objects.create(
            name="Smartphone",
            active=True,
            category=Category.objects.create(name="Media", active=True),
        )  # Product from another category

        response = self.client.get(
            reverse("product-list"), data={"category_id": category.id}
        )
        self.assertEqual(response.status_code, 200)

        expected = [
            {
                "id": product.id,
                "date_created": self.format_datetime(product.date_created),
                "date_updated": self.format_datetime(product.date_updated),
                "name": product.name,
                "category": category.id,
            }
        ]
        self.assertEqual(response.json(), expected)

    def test_create_not_allowed(self):
        category = Category.objects.create(name="Personal Care", active=True)
        assert not Product.objects.exists()

        response = self.client.post(
            reverse("product-list"),
            data={
                "name": "Toothbrush",
                "category": category.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(Product.objects.exists())

    def test_update_not_allowed(self):
        category = Category.objects.create(name="Personal Care", active=True)
        product = Product.objects.create(
            name="Toothbrush", active=True, category=category
        )

        response = self.client.put(
            reverse("product-detail", args=[product.id]),
            data={
                "name": "Toothbrush (updated)",
                "category": category.id,
                "active": False,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        product.refresh_from_db()
        self.assertEqual(product.name, "Toothbrush")
        self.assertTrue(product.active)

    def test_delete_not_allowed(self):
        category = Category.objects.create(name="Personal Care", active=True)
        product = Product.objects.create(
            name="Toothbrush", active=True, category=category
        )

        response = self.client.delete(reverse("product-detail", args=[product.id]))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn(product, Product.objects.all())
