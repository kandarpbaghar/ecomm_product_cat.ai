from datetime import datetime
from database import db
from sqlalchemy import Numeric

class SKU(db.Model):
    __tablename__ = 'skus'
    
    id = db.Column(db.Integer, primary_key=True)
    shopify_id = db.Column(db.String(50), unique=True, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    handle = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    body_html = db.Column(db.Text)
    vendor = db.Column(db.String(255))
    product_type = db.Column(db.String(255))
    tags = db.Column(db.Text)  # Comma-separated tags
    status = db.Column(db.String(50), default='active')  # active, archived, draft
    
    # Pricing
    price = db.Column(Numeric(10, 2))
    compare_at_price = db.Column(Numeric(10, 2))
    taxable = db.Column(db.Boolean, default=True)
    
    # Inventory
    sku_code = db.Column(db.String(100), unique=True)
    barcode = db.Column(db.String(100))
    track_quantity = db.Column(db.Boolean, default=True)
    quantity = db.Column(db.Integer, default=0)
    inventory_policy = db.Column(db.String(20), default='deny')  # deny, continue
    
    # Shipping
    requires_shipping = db.Column(db.Boolean, default=True)
    weight = db.Column(db.Float)
    weight_unit = db.Column(db.String(10), default='kg')
    fulfillment_service = db.Column(db.String(50), default='manual')  # manual, automatic
    
    # SEO
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    
    # Vector store reference
    weaviate_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Shopify-specific fields
    template_suffix = db.Column(db.String(255))
    published_scope = db.Column(db.String(50), default='web')
    admin_graphql_api_id = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    categories = db.relationship('Category', secondary='product_categories', back_populates='products')
    images = db.relationship('SKUImage', backref='sku', lazy=True, cascade='all, delete-orphan')
    variants = db.relationship('SKUVariant', backref='sku', lazy=True, cascade='all, delete-orphan')
    options = db.relationship('ProductOption', backref='sku', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'shopify_id': self.shopify_id,
            'title': self.title,
            'handle': self.handle,
            'description': self.description,
            'body_html': self.body_html,
            'vendor': self.vendor,
            'product_type': self.product_type,
            'tags': self.tags.split(',') if self.tags else [],
            'status': self.status,
            'price': float(self.price) if self.price else None,
            'compare_at_price': float(self.compare_at_price) if self.compare_at_price else None,
            'taxable': self.taxable,
            'sku_code': self.sku_code,
            'barcode': self.barcode,
            'track_quantity': self.track_quantity,
            'quantity': self.quantity,
            'inventory_policy': self.inventory_policy,
            'fulfillment_service': self.fulfillment_service,
            'requires_shipping': self.requires_shipping,
            'weight': self.weight,
            'weight_unit': self.weight_unit,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'weaviate_id': self.weaviate_id,
            'template_suffix': self.template_suffix,
            'published_scope': self.published_scope,
            'admin_graphql_api_id': self.admin_graphql_api_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'images': [img.to_dict() for img in self.images],
            'variants': [var.to_dict() for var in self.variants],
            'options': [opt.to_dict() for opt in self.options],
            'categories': [{'id': cat.id, 'name': cat.name} for cat in self.categories]
        }


class SKUImage(db.Model):
    __tablename__ = 'sku_images'
    
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False)
    shopify_id = db.Column(db.String(50), unique=True, nullable=True)
    url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(255))
    position = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    variant_ids = db.Column(db.Text)  # JSON array of variant IDs
    admin_graphql_api_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'shopify_id': self.shopify_id,
            'url': self.url,
            'alt_text': self.alt_text,
            'position': self.position,
            'width': self.width,
            'height': self.height
        }


class SKUVariant(db.Model):
    __tablename__ = 'sku_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False)
    shopify_id = db.Column(db.String(50), unique=True, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(Numeric(10, 2))
    compare_at_price = db.Column(Numeric(10, 2))
    sku_code = db.Column(db.String(100))
    barcode = db.Column(db.String(100))
    weight = db.Column(db.Float)
    weight_unit = db.Column(db.String(10), default='kg')
    inventory_quantity = db.Column(db.Integer, default=0)
    
    # Shopify business fields
    inventory_policy = db.Column(db.String(50), default='deny')  # deny/continue
    fulfillment_service = db.Column(db.String(50), default='manual')  # manual/automatic
    taxable = db.Column(db.Boolean, default=True)
    grams = db.Column(db.Integer)  # Weight in grams
    image_id = db.Column(db.String(50))  # Associated image ID
    inventory_item_id = db.Column(db.String(50))  # Shopify inventory item ID
    old_inventory_quantity = db.Column(db.Integer)  # Previous quantity
    requires_shipping = db.Column(db.Boolean, default=True)
    admin_graphql_api_id = db.Column(db.String(255))
    
    # Variant options
    option1 = db.Column(db.String(255))
    option2 = db.Column(db.String(255))
    option3 = db.Column(db.String(255))
    
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'shopify_id': self.shopify_id,
            'title': self.title,
            'price': float(self.price) if self.price else None,
            'compare_at_price': float(self.compare_at_price) if self.compare_at_price else None,
            'sku_code': self.sku_code,
            'barcode': self.barcode,
            'weight': self.weight,
            'weight_unit': self.weight_unit,
            'inventory_quantity': self.inventory_quantity,
            'inventory_policy': self.inventory_policy,
            'fulfillment_service': self.fulfillment_service,
            'taxable': self.taxable,
            'grams': self.grams,
            'image_id': self.image_id,
            'inventory_item_id': self.inventory_item_id,
            'old_inventory_quantity': self.old_inventory_quantity,
            'requires_shipping': self.requires_shipping,
            'admin_graphql_api_id': self.admin_graphql_api_id,
            'option1': self.option1,
            'option2': self.option2,
            'option3': self.option3,
            'position': self.position
        }


class ProductOption(db.Model):
    __tablename__ = 'product_options'
    
    id = db.Column(db.Integer, primary_key=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('skus.id'), nullable=False)
    shopify_id = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)  # Size, Color, Material, etc.
    position = db.Column(db.Integer, default=0)
    values = db.Column(db.Text)  # JSON array of values: ["Small", "Medium", "Large"]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'shopify_id': self.shopify_id,
            'name': self.name,
            'position': self.position,
            'values': json.loads(self.values) if self.values else []
        }