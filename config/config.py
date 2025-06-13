import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '../ai_ecomm_cat.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Weaviate configuration
    WEAVIATE_URL = os.environ.get('WEAVIATE_URL') or 'http://localhost:8080'
    WEAVIATE_API_KEY = os.environ.get('WEAVIATE_API_KEY')
    
    # Shopify configuration
    SHOPIFY_STORE_URL = os.environ.get('SHOPIFY_STORE_URL')
    SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
    SHOPIFY_API_VERSION = '2024-01'
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, '../uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # API configuration
    API_TITLE = 'AI E-commerce Product Search API'
    API_VERSION = 'v1'
    
    # Pagination
    ITEMS_PER_PAGE = 20