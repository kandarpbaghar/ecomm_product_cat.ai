# AI E-commerce Product Search

An AI-powered product search application with vector search capabilities for images and descriptions, integrated with Shopify.

## Features

- **Vector Search**: Search products using text descriptions or images
- **Image Search**: Upload product images to find similar products
- **Shopping Agent**: Coversational shopping agent with option to add to cart inside the agent.
- **Shopify Integration**: Sync products and categories from Shopify store
- **CRUD Operations**: Manage categories and SKUs
- **REST API**: Full API for all operations
- **Multi-database Support**: SQLite by default, easily configurable for other databases

## Prerequisites

- Python 3.8+
- Weaviate vector database (local or cloud)
- Shopify store with API access (optional)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd product_cat.ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment variables:
```bash
cp .env.example .env
```

5. Configure your `.env` file with your settings

## Running Weaviate

### Option 1: Docker (Recommended)
```bash
docker run -d \
  -p 8080:8080 \
  -p 50051:50051 \
  -e QUERY_DEFAULTS_LIMIT=25 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
  -e DEFAULT_VECTORIZER_MODULE='multi2vec-clip' \
  -e ENABLE_MODULES='multi2vec-clip' \
  -e CLIP_INFERENCE_API='http://multi2vec-clip:8080' \
  --name weaviate \
  semitechnologies/weaviate:latest
```

### Option 2: Embedded (Development)
The application will automatically use embedded Weaviate if no external instance is configured.

## Running the Application

1. Initialize the database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

2. Run the application:
```bash
python ai_ecomm.py
```

3. Access the application:
- Main interface: http://localhost:8082
- Search page: http://localhost:8082/search
- API endpoints: http://localhost:8082/api/*

## API Endpoints

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create a category
- `GET /api/categories/{id}` - Get a category
- `PUT /api/categories/{id}` - Update a category
- `DELETE /api/categories/{id}` - Delete a category

### SKUs
- `GET /api/skus` - List all SKUs
- `POST /api/skus` - Create a SKU
- `GET /api/skus/{id}` - Get a SKU
- `PUT /api/skus/{id}` - Update a SKU
- `DELETE /api/skus/{id}` - Delete a SKU

### Search
- `POST /api/search` - Search by text or image
  - Text search: `type=text, query=<search_text>`
  - Image search: `type=image, image=<file>`

### Shopify Sync
- `POST /api/sync/shopify` - Start sync from Shopify
- `GET /api/sync/status/{id}` - Check sync status

## Shopify Integration

1. Create a private app in your Shopify admin
2. Grant necessary permissions (read products, collections)
3. Add credentials to `.env`:
   ```
   SHOPIFY_STORE_URL=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=your-access-token
   ```

## Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use a production database (PostgreSQL recommended)
3. Use a production WSGI server:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 'ai_ecomm:create_app()'
   ```

## License

MIT
