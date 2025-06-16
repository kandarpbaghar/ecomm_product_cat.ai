from flask import Flask, render_template, send_from_directory
import os
import warnings
from config.config import Config
from database import db, migrate

# Suppress Weaviate deprecation warnings for cleaner logs
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models and create tables
    with app.app_context():
        from models import Category, SKU, SKUImage, SKUVariant, SyncLog, AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics
        from models.sku import ProductOption
        db.create_all()
    
    # Register blueprints
    from blueprints.ai_ecomm_cat import ai_ecomm_cat_bp
    from blueprints.shopping_agent_bp import shopping_agent_bp
    app.register_blueprint(ai_ecomm_cat_bp, url_prefix='/api')
    app.register_blueprint(shopping_agent_bp)
    
    # Routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/search')
    def search_page():
        return render_template('search.html')
    
    @app.route('/admin/categories')
    def admin_categories():
        return render_template('categories.html')
    
    @app.route('/admin/skus')
    def admin_skus():
        return render_template('skus.html')
    
    @app.route('/admin/shopify')
    def admin_shopify():
        return render_template('shopify_management.html')
    
    @app.route('/admin/vector')
    def admin_vector():
        return render_template('vector_config.html')
    
    @app.route('/admin/settings')
    def admin_settings():
        return render_template('settings.html')
    
    @app.route('/catalog')
    def catalog():
        return render_template('catalog.html')
    
    @app.route('/catalog/customer')
    def catalog_customer():
        return render_template('catalog_customer.html')
    
    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        return render_template('product_detail.html', product_id=product_id)
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve uploaded images"""
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        return send_from_directory(upload_dir, filename)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8082)