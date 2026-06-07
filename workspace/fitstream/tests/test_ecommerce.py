"""Tests for e-commerce connector."""

import os
import tempfile
import pytest
from fitstream.core.ecommerce import ECommerceConnector, ECommerceConfig, Product


@pytest.fixture
def connector():
    with tempfile.TemporaryDirectory() as d:
        config = ECommerceConfig(platform="shopify", shop_url="test.myshopify.com")
        yield ECommerceConnector(config, data_dir=d)


class TestProductIngestion:
    def test_ingest_shopify_product(self, connector):
        data = {
            "id": 12345,
            "title": "Blue Cotton T-Shirt",
            "body_html": "A comfortable blue cotton t-shirt",
            "product_type": "tops",
            "images": [{"src": "https://cdn.shopify.com/shirt.jpg"}],
            "variants": [{"price": "29.99"}],
            "tags": "casual, summer",
        }
        product = connector.ingest_product(data)
        assert product.id == "12345"
        assert product.title == "Blue Cotton T-Shirt"
        assert product.category == "upper"
        assert len(product.images) == 1

    def test_ingest_dress(self, connector):
        data = {"id": "d1", "title": "Red Evening Dress", "product_type": "dresses",
                "images": [{"src": "img.jpg"}]}
        p = connector.ingest_product(data)
        assert p.category == "dress"

    def test_ingest_shoes(self, connector):
        data = {"id": "s1", "title": "White Sneakers", "product_type": "shoes",
                "images": ["shoe.jpg"]}
        p = connector.ingest_product(data)
        assert p.category == "shoes"

    def test_ingest_no_images(self, connector):
        data = {"id": "n1", "title": "Hat"}
        p = connector.ingest_product(data)
        assert len(p.images) == 0


class TestCatalog:
    def test_list_products(self, connector):
        connector.ingest_product({"id": "1", "title": "Shirt", "product_type": "tops"})
        connector.ingest_product({"id": "2", "title": "Pants", "product_type": "pants"})
        
        all_prods = connector.list_products()
        assert len(all_prods) == 2
        
        upper = connector.list_products(category="upper")
        assert len(upper) == 1

    def test_get_product(self, connector):
        connector.ingest_product({"id": "g1", "title": "Test"})
        assert connector.get_product("g1") is not None
        assert connector.get_product("nonexistent") is None

    def test_pending_products(self, connector):
        connector.ingest_product({"id": "p1", "title": "Pending"})
        pending = connector.get_pending_products()
        assert len(pending) == 1
        assert pending[0].tryon_video_path is None


class TestWebhookVerification:
    def test_no_secret_always_passes(self, connector):
        assert connector.verify_webhook_signature(b"any", "any") is True

    def test_with_secret(self):
        config = ECommerceConfig(platform="shopify", webhook_secret="mysecret")
        with tempfile.TemporaryDirectory() as d:
            conn = ECommerceConnector(config, data_dir=d)
            
            import hmac, hashlib
            body = b'{"test": true}'
            sig = hmac.new(b"mysecret", body, hashlib.sha256).hexdigest()
            
            assert conn.verify_webhook_signature(body, sig) is True
            assert conn.verify_webhook_signature(body, "wrong") is False


class TestPersistence:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            config = ECommerceConfig(platform="test")
            c1 = ECommerceConnector(config, data_dir=d)
            c1.ingest_product({"id": "persist", "title": "Persistent Product",
                              "images": ["img.jpg"]})
            
            c2 = ECommerceConnector(config, data_dir=d)
            assert c2.get_product("persist") is not None
            assert c2.get_product("persist").title == "Persistent Product"


class TestProduct:
    def test_to_dict(self):
        p = Product(id="1", title="Test", category="upper")
        d = p.to_dict()
        assert d["id"] == "1"
        assert d["has_tryon_video"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
