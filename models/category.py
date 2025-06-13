from datetime import datetime
from database import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    shopify_id = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    handle = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    products = db.relationship('SKU', secondary='product_categories', back_populates='categories')
    
    def to_dict(self):
        return {
            'id': self.id,
            'shopify_id': self.shopify_id,
            'name': self.name,
            'handle': self.handle,
            'description': self.description,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Association table for many-to-many relationship between products and categories
product_categories = db.Table('product_categories',
    db.Column('sku_id', db.Integer, db.ForeignKey('skus.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)