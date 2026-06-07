"""
FitStream E-Commerce Integration
Connect with Shopify, WooCommerce, and custom stores.

Features:
  - Webhook receiver for new product events
  - Auto-generate try-on videos for new products
  - Product catalog sync
  - Batch video generation for entire catalogs
  - Video hosting URL generation

Usage:
    # Shopify webhook handler
    connector = ShopifyConnector(shop_url="myshop.myshopify.com", api_key="...")
    
    # Auto-generate try-on video when new product is added
    connector.on_product_created(product_data)
    
    # Batch generate for catalog
    connector.generate_catalog_videos(model_image="model.jpg")
"""

import os
import json
import hmac
import hashlib
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Product:
    """A product from an e-commerce store."""
    id: str
    title: str
    description: str = ""
    images: List[str] = field(default_factory=list)   # Product image URLs
    category: str = ""          # upper, lower, dress, shoes, accessories
    price: str = ""
    sku: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""            # shopify, woocommerce, custom
    
    # Generated content
    tryon_video_path: Optional[str] = None
    animation_video_path: Optional[str] = None
    generated_at: Optional[float] = None
    
    def to_dict(self) -> dict:
        """To dict."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "images": len(self.images),
            "has_tryon_video": self.tryon_video_path is not None,
            "has_animation": self.animation_video_path is not None,
        }


@dataclass
class ECommerceConfig:
    """Configuration for e-commerce integration."""
    platform: str              # shopify, woocommerce, custom
    shop_url: str = ""
    api_key: str = ""
    api_secret: str = ""
    webhook_secret: str = ""
    
    # Auto-generation settings
    auto_generate: bool = True
    default_model_image: str = ""   # Default person image for try-on
    default_style: str = "cinematic"
    default_preset: str = "draft"
    default_action: str = "walking naturally, showing the outfit"
    
    # Category mapping
    category_map: Dict[str, str] = field(default_factory=lambda: {
        "tops": "upper", "shirts": "upper", "blouses": "upper",
        "pants": "lower", "jeans": "lower", "shorts": "lower", "skirts": "lower",
        "dresses": "dress", "gowns": "dress",
        "shoes": "shoes", "boots": "shoes", "sneakers": "shoes",
        "bags": "accessories", "jewelry": "accessories", "hats": "accessories",
    })


class ECommerceConnector:
    """
    Base e-commerce connector.
    Handles product ingestion and video generation.
    """
    
    def __init__(self, config: ECommerceConfig, data_dir: str = "./data/ecommerce") -> None:
        self.config = config
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self._products: Dict[str, Product] = {}
        self._load_catalog()
    
    def ingest_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Ingest a product from webhook or API.
        Normalizes the data into our Product format.
        """
        product = Product(
            id=str(product_data.get("id", "")),
            title=product_data.get("title", ""),
            description=product_data.get("description", product_data.get("body_html", "")),
            images=self._extract_images(product_data),
            category=self._detect_category(product_data),
            price=str(product_data.get("price", product_data.get("variants", [{}])[0].get("price", ""))),
            sku=product_data.get("sku", ""),
            tags=product_data.get("tags", "").split(",") if isinstance(product_data.get("tags"), str) else product_data.get("tags", []),
            source=self.config.platform,
        )
        
        self._products[product.id] = product
        self._save_catalog()
        
        logger.info(f"🛒 Product ingested: {product.title} (id={product.id}, cat={product.category})")
        return product
    
    def _extract_images(self, data: Dict[str, Any]) -> List[str]:
        images = []
        
        # Shopify format
        if "images" in data:
            for img in data["images"]:
                if isinstance(img, dict):
                    images.append(img.get("src", ""))
                elif isinstance(img, str):
                    images.append(img)
        
        # WooCommerce format
        if "featured_image" in data:
            images.append(data["featured_image"])
        
        # Direct image URL
        if "image" in data and isinstance(data["image"], str):
            images.append(data["image"])
        if "image" in data and isinstance(data["image"], dict):
            images.append(data["image"].get("src", ""))
        
        return [img for img in images if img]
    
    def _detect_category(self, data: Dict[str, Any]) -> str:
        searchable = (
            data.get("title", "") + " " +
            data.get("product_type", "") + " " +
            data.get("category", "") + " " +
            str(data.get("tags", ""))
        ).lower()
        
        for keyword, category in self.config.category_map.items():
            if keyword in searchable:
                return category
        
        return "upper"  # default
    
    def get_product(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)
    
    def list_products(self, category: Optional[str] = None) -> List[dict]:
        """Get product."""
        products = list(self._products.values())
        if category:
            products = [p for p in products if p.category == category]
        return [p.to_dict() for p in products]
    
    def get_pending_products(self) -> List[Product]:
        """List ingested products."""
        """Get products that don't have videos yet."""
        return [p for p in self._products.values() if p.tryon_video_path is None]
    
    def generate_product_video(
        self,
        product_id: str,
        model_image: Optional[str] = None,
        style: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a try-on or animation video for a product.
        Returns the video path or None on failure.
        """
        product = self._products.get(product_id)
        if not product:
            logger.error(f"Product {product_id} not found")
            return None
        
        if not product.images:
            logger.error(f"Product {product_id} has no images")
            return None
        
        model_img = model_image or self.config.default_model_image
        if not model_img:
            logger.error("No model image specified")
            return None
        
        logger.info(f"🛒 Generating video for: {product.title}")
        
        try:
            from fitstream.core.pipelines.tryon import TryOnPipeline
            from fitstream.config import get_config
            
            config = get_config()
            pipeline = TryOnPipeline(config)
            
            result = pipeline.generate(
                person_image=model_img,
                garment_image=product.images[0],
                prompt=product.title,
                category=product.category,
                action=self.config.default_action,
                style=style or self.config.default_style,
                preset=self.config.default_preset,
            )
            
            if result.success:
                product.tryon_video_path = result.video_path
                product.generated_at = time.time()
                self._save_catalog()
                logger.success(f"🛒 Video generated: {product.title} → {result.video_path}")
                return result.video_path
            else:
                logger.error(f"🛒 Video generation failed: {result.error}")
                return None
                
        except (OSError, ValueError, KeyError) as e:
            logger.error(f"🛒 Error: {e}")
            return None
    
    def generate_catalog(
        self,
        model_image: str,
        max_products: int = 50,
        style: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Batch generate videos for all pending products.
        Returns a summary of results.
        """
        pending = self.get_pending_products()[:max_products]
        
        if not pending:
            return {"generated": 0, "message": "No pending products"}
        
        logger.info(f"🛒 Batch generating {len(pending)} product videos...")
        
        results = {"generated": 0, "failed": 0, "products": []}
        
        for product in pending:
            video_path = self.generate_product_video(
                product.id, model_image=model_image, style=style,
            )
            
            if video_path:
                results["generated"] += 1
            else:
                results["failed"] += 1
            
            results["products"].append({
                "id": product.id,
                "title": product.title,
                "success": video_path is not None,
            })
        
        logger.info(
            f"🛒 Catalog batch complete: {results['generated']} generated, "
            f"{results['failed']} failed"
        )
        return results
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        if not self.config.webhook_secret:
            return True  # No secret configured = accept all
        
        expected = hmac.new(
            self.config.webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        
        # Shopify sends as base64, WooCommerce as hex
        return hmac.compare_digest(expected, signature.replace("sha256=", ""))
    
    def _save_catalog(self) -> None:
        """Verify a Shopify/WooCommerce webhook signature."""
        try:
            data = {
                pid: {
                    "id": p.id, "title": p.title, "description": p.description,
                    "images": p.images, "category": p.category,
                    "price": p.price, "sku": p.sku, "tags": p.tags,
                    "source": p.source,
                    "tryon_video_path": p.tryon_video_path,
                    "animation_video_path": p.animation_video_path,
                    "generated_at": p.generated_at,
                }
                for pid, p in self._products.items()
            }
            with open(os.path.join(self.data_dir, "catalog.json"), "w") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Catalog save failed: {e}")
    
    def _load_catalog(self) -> None:
        path = os.path.join(self.data_dir, "catalog.json")
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
            for pid, pd in data.items():
                self._products[pid] = Product(
                    **{k: v for k, v in pd.items() if k in Product.__dataclass_fields__}
                )
            if self._products:
                logger.info(f"🛒 Catalog loaded: {len(self._products)} products")
        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Catalog load failed: {e}")
