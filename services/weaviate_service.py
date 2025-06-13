import weaviate
from weaviate.embedded import EmbeddedOptions
import os
from typing import List, Dict, Optional
import base64
from PIL import Image
import io
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from .openai_service import OpenAIService

class WeaviateService:
    def __init__(self, url: str = None, api_key: str = None, vectorizer: str = None):
        # First try parameters, then environment, then database config
        self.url = url or self._get_config_value('weaviate_url') or os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        self.api_key = api_key or self._get_config_value('api_key') or os.getenv('WEAVIATE_API_KEY')
        self.vectorizer = vectorizer or self._get_config_value('vectorizer') or os.getenv('WEAVIATE_VECTORIZER', 'text2vec-transformers')
        self.timeout = self._get_config_value('timeout') or 30
        self.client = None
        
        print(f"[WEAVIATE] Initializing with URL: {self.url}, Vectorizer: {self.vectorizer}, API Key: {'***' if self.api_key else 'None'}")
        
        # Initialize sentence transformer for manual vectorization
        try:
            print(f"[WEAVIATE] Loading sentence transformer model...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            print(f"[WEAVIATE] Sentence transformer loaded successfully")
        except Exception as e:
            print(f"[WEAVIATE] Failed to load sentence transformer: {e}")
            self.sentence_model = None
        
        # Initialize OpenAI service for image embeddings
        try:
            self.openai_service = OpenAIService()
            if self.openai_service.is_configured():
                print(f"[WEAVIATE] OpenAI service initialized for image embeddings")
            else:
                print(f"[WEAVIATE] OpenAI not configured - image search will use fallback")
        except Exception as e:
            print(f"[WEAVIATE] Failed to initialize OpenAI service: {e}")
            self.openai_service = None
        
        self.connect()
        self.setup_schema()
    
    def _get_config_value(self, key):
        """Get configuration value from database"""
        try:
            # Import here to avoid circular imports
            from database import db
            from sqlalchemy import text
            
            # Check if config table exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_config'"))
            if not result.fetchone():
                return None
            
            # Get the latest config
            config = db.session.execute(text("SELECT * FROM vector_config ORDER BY id DESC LIMIT 1")).fetchone()
            if not config:
                return None
            
            # Map column indices to values
            config_map = {
                'weaviate_url': config[1],
                'api_key': config[2],
                'vectorizer': config[3],
                'timeout': config[4]
            }
            
            return config_map.get(key)
            
        except Exception as e:
            print(f"Error getting config value {key}: {e}")
            return None
    
    def connect(self):
        """Connect to Weaviate instance"""
        print(f"[WEAVIATE] Attempting to connect to {self.url}")
        try:
            if self.api_key:
                print(f"[WEAVIATE] Using API key authentication")
                auth_config = weaviate.AuthApiKey(api_key=self.api_key)
                self.client = weaviate.Client(
                    url=self.url,
                    auth_client_secret=auth_config
                )
            else:
                print(f"[WEAVIATE] Using no authentication (local development)")
                # For local development without authentication
                self.client = weaviate.Client(url=self.url)
                
            # Test the connection
            self.client.schema.get()
            print(f"[WEAVIATE] Successfully connected to Weaviate at {self.url}")
            
        except Exception as e:
            print(f"[WEAVIATE] Failed to connect to Weaviate at {self.url}: {e}")
            print(f"[WEAVIATE] Falling back to embedded Weaviate")
            # Use embedded Weaviate for development
            try:
                self.client = weaviate.Client(
                    embedded_options=EmbeddedOptions()
                )
                print(f"[WEAVIATE] Successfully connected to embedded Weaviate")
            except Exception as embedded_e:
                print(f"[WEAVIATE] Failed to connect to embedded Weaviate: {embedded_e}")
                raise
    
    def _generate_vector(self, text: str) -> List[float]:
        """Generate vector embedding for text using sentence transformer"""
        if not self.sentence_model or not text:
            return None
        
        try:
            # Generate embedding
            embedding = self.sentence_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"[WEAVIATE] Error generating vector for text: {e}")
            return None
    
    def setup_schema(self):
        """Setup Weaviate schema for products"""
        # Configure module config based on vectorizer
        module_config = {}
        if self.vectorizer == "text2vec-transformers":
            module_config = {
                "text2vec-transformers": {
                    "poolingStrategy": "masked_mean",
                    "vectorizeClassName": True
                }
            }
        elif self.vectorizer == "text2vec-openai":
            module_config = {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            }
        elif self.vectorizer == "multi2vec-clip":
            module_config = {
                "multi2vec-clip": {
                    "textFields": ["title", "description", "tags"],
                    "imageFields": ["image"]
                }
            }
        
        # For now, use manual vectorization (no vectorizer module required)
        schema = {
            "classes": [{
                "class": "Product",
                "description": "E-commerce product with text and image search capabilities",
                "vectorizer": "none",  # Use manual vectors
                "properties": [
                    {
                        "name": "product_id",
                        "dataType": ["int"],
                        "description": "Database ID of the product"
                    },
                    {
                        "name": "shopify_id",
                        "dataType": ["string"],
                        "description": "Shopify ID of the product"
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Product title"
                    },
                    {
                        "name": "description",
                        "dataType": ["text"],
                        "description": "Product description"
                    },
                    {
                        "name": "tags",
                        "dataType": ["text"],
                        "description": "Product tags"
                    },
                    {
                        "name": "vendor",
                        "dataType": ["string"],
                        "description": "Product vendor"
                    },
                    {
                        "name": "product_type",
                        "dataType": ["string"],
                        "description": "Product type"
                    },
                    {
                        "name": "price",
                        "dataType": ["number"],
                        "description": "Product price"
                    },
                    {
                        "name": "image",
                        "dataType": ["blob"],
                        "description": "Product image for visual search"
                    },
                    {
                        "name": "image_url",
                        "dataType": ["string"],
                        "description": "URL of the product image"
                    },
                    {
                        "name": "image_description",
                        "dataType": ["text"],
                        "description": "AI-generated description of the product image"
                    },
                    {
                        "name": "image_embedding",
                        "dataType": ["number[]"],
                        "description": "Image embedding vector"
                    },
                    {
                        "name": "categories",
                        "dataType": ["string[]"],
                        "description": "Product categories"
                    }
                ]
            }]
        }
        
        try:
            # Check if schema already exists
            existing_schema = self.client.schema.get()
            if not any(c['class'] == 'Product' for c in existing_schema.get('classes', [])):
                self.client.schema.create(schema)
                print("Weaviate schema created successfully")
            else:
                print("Weaviate schema already exists")
        except Exception as e:
            print(f"Error setting up Weaviate schema: {e}")
    
    def add_product(self, product_data: Dict) -> Optional[str]:
        """Add a product to Weaviate"""
        try:
            print(f"[WEAVIATE] Adding product: {product_data.get('title', 'Unknown')}")
            
            # Prepare data for Weaviate
            weaviate_data = {
                "product_id": product_data['id'],
                "shopify_id": product_data.get('shopify_id'),
                "title": product_data['title'],
                "description": product_data.get('description', ''),
                "tags": ', '.join(product_data.get('tags', [])) if isinstance(product_data.get('tags'), list) else str(product_data.get('tags', '')),
                "vendor": product_data.get('vendor', ''),
                "product_type": product_data.get('product_type', ''),
                "price": float(product_data.get('price', 0)),
                "categories": [cat['name'] for cat in product_data.get('categories', [])]
            }
            
            # Handle image and generate embeddings
            if product_data.get('images') and len(product_data['images']) > 0:
                image_url = product_data['images'][0]['url']
                weaviate_data['image_url'] = image_url
                
                # Download and encode image
                image_base64 = self._download_and_encode_image(image_url)
                if image_base64:
                    weaviate_data['image'] = image_base64
                    
                    # Generate image description and embedding using OpenAI
                    if self.openai_service and self.openai_service.is_configured():
                        print(f"[WEAVIATE] Generating image embedding for {product_data.get('title', 'Unknown')}")
                        image_data = self.openai_service.process_image_for_embedding(image_base64)
                        if image_data:
                            weaviate_data['image_description'] = image_data['description']
                            weaviate_data['image_embedding'] = image_data['embedding']
                            print(f"[WEAVIATE] Image embedding generated successfully")
                        else:
                            print(f"[WEAVIATE] Failed to generate image embedding")
                    else:
                        print(f"[WEAVIATE] OpenAI not configured for image embedding")
            
            # Generate vector manually for text search
            tags_text = ', '.join(product_data.get('tags', [])) if isinstance(product_data.get('tags'), list) else str(product_data.get('tags', ''))
            text_for_vector = f"{product_data['title']} {product_data.get('description', '')} {tags_text} {product_data.get('vendor', '')} {product_data.get('product_type', '')}"
            vector = self._generate_vector(text_for_vector)
            
            if vector:
                print(f"[WEAVIATE] Generated vector with {len(vector)} dimensions")
                # Add to Weaviate with manual vector
                result = self.client.data_object.create(
                    data_object=weaviate_data,
                    class_name="Product",
                    vector=vector
                )
            else:
                print(f"[WEAVIATE] No vector generated, adding without vector")
                # Add to Weaviate without vector
                result = self.client.data_object.create(
                    data_object=weaviate_data,
                    class_name="Product"
                )
            
            print(f"[WEAVIATE] Successfully added product with ID: {result}")
            return result
            
        except Exception as e:
            print(f"[WEAVIATE] Error adding product to Weaviate: {e}")
            import traceback
            print(f"[WEAVIATE] Full traceback: {traceback.format_exc()}")
            return None
    
    def update_product(self, weaviate_id: str, product_data: Dict) -> bool:
        """Update a product in Weaviate"""
        try:
            # Prepare update data
            update_data = {
                "title": product_data['title'],
                "description": product_data.get('description', ''),
                "tags": ', '.join(product_data.get('tags', [])) if isinstance(product_data.get('tags'), list) else str(product_data.get('tags', '')),
                "vendor": product_data.get('vendor', ''),
                "product_type": product_data.get('product_type', ''),
                "price": float(product_data.get('price', 0)),
                "categories": [cat['name'] for cat in product_data.get('categories', [])]
            }
            
            # Handle image update
            if product_data.get('images') and len(product_data['images']) > 0:
                image_url = product_data['images'][0]['url']
                update_data['image_url'] = image_url
                
                # Download and encode image
                image_base64 = self._download_and_encode_image(image_url)
                if image_base64:
                    update_data['image'] = image_base64
            
            # Update in Weaviate
            self.client.data_object.update(
                data_object=update_data,
                class_name="Product",
                uuid=weaviate_id
            )
            
            return True
        except Exception as e:
            print(f"Error updating product in Weaviate: {e}")
            return False
    
    def delete_product(self, weaviate_id: str) -> bool:
        """Delete a product from Weaviate"""
        try:
            self.client.data_object.delete(
                uuid=weaviate_id,
                class_name="Product"
            )
            return True
        except Exception as e:
            print(f"Error deleting product from Weaviate: {e}")
            return False
    
    def search_by_text(self, query: str, limit: int = 10) -> List[Dict]:
        """Search products by text query using vector similarity"""
        print(f"[WEAVIATE] Starting text search for query: '{query}'")
        print(f"[WEAVIATE] Using URL: {self.url}, Vectorizer: {self.vectorizer}")
        
        try:
            # First check if we have any products indexed
            count_result = (
                self.client.query
                .aggregate("Product")
                .with_meta_count()
                .do()
            )
            
            total_products = count_result.get('data', {}).get('Aggregate', {}).get('Product', [{}])[0].get('meta', {}).get('count', 0)
            print(f"[WEAVIATE] Total products indexed in Weaviate: {total_products}")
            
            if total_products == 0:
                print(f"[WEAVIATE] No products indexed in Weaviate, will fall back to database search")
                return []
            
            # Generate vector for the search query
            print(f"[WEAVIATE] Generating vector for search query...")
            query_vector = self._generate_vector(query)
            
            if not query_vector:
                print(f"[WEAVIATE] Failed to generate vector for query, falling back")
                return []
            
            # Use manual vector search
            print(f"[WEAVIATE] Performing vector search with {len(query_vector)} dimensions...")
            result = (
                self.client.query
                .get("Product", ["product_id", "title", "description", "price", "image_url", "vendor", "product_type", "tags"])
                .with_near_vector({"vector": query_vector})
                .with_limit(limit)
                .with_additional(["distance", "score"])
                .do()
            )
            
            products = result.get('data', {}).get('Get', {}).get('Product', [])
            print(f"[WEAVIATE] Vector search returned {len(products)} results")
            
            if products:
                print(f"[WEAVIATE] First result: {products[0].get('title', 'No title')} (distance: {products[0].get('_additional', {}).get('distance', 'N/A')})")
            
            return products
        except Exception as e:
            print(f"[WEAVIATE] Error searching by text vector: {e}")
            import traceback
            print(f"[WEAVIATE] Full traceback: {traceback.format_exc()}")
            
            # Fallback to keyword-based search if vector search fails
            try:
                where_filter = {
                    "operator": "Or",
                    "operands": [
                        {
                            "path": ["title"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        },
                        {
                            "path": ["description"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        },
                        {
                            "path": ["tags"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        },
                        {
                            "path": ["vendor"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        },
                        {
                            "path": ["product_type"],
                            "operator": "Like",
                            "valueText": f"*{query}*"
                        }
                    ]
                }
                
                result = (
                    self.client.query
                    .get("Product", ["product_id", "title", "description", "price", "image_url", "vendor", "product_type", "tags"])
                    .with_where(where_filter)
                    .with_limit(limit)
                    .do()
                )
                
                products = result.get('data', {}).get('Get', {}).get('Product', [])
                return products
            except Exception as fallback_e:
                print(f"Error in fallback text search: {fallback_e}")
                return []
    
    def search_by_image(self, image_base64: str, limit: int = 10) -> List[Dict]:
        """Search products by image using OpenAI embeddings"""
        print(f"[WEAVIATE] Starting image search")
        
        try:
            # First, check if we have any products with image embeddings
            count_result = (
                self.client.query
                .aggregate("Product")
                .with_meta_count()
                .do()
            )
            
            total_products = count_result.get('data', {}).get('Aggregate', {}).get('Product', [{}])[0].get('meta', {}).get('count', 0)
            print(f"[WEAVIATE] Total products indexed: {total_products}")
            
            if total_products == 0:
                print(f"[WEAVIATE] No products indexed")
                return []
            
            # Use OpenAI for image similarity search
            if self.openai_service and self.openai_service.is_configured():
                print(f"[WEAVIATE] Using OpenAI for image search")
                
                # Generate embedding for query image
                query_embedding = self.openai_service.get_image_embedding(image_base64)
                if not query_embedding:
                    print(f"[WEAVIATE] Failed to generate query image embedding")
                    return self._fallback_image_search(limit)
                
                print(f"[WEAVIATE] Generated query embedding with {len(query_embedding)} dimensions")
                
                # Get all products with image embeddings
                result = (
                    self.client.query
                    .get("Product", ["product_id", "title", "description", "price", "image_url", "vendor", "product_type", "image_embedding", "image_description"])
                    .with_limit(100)  # Get more to calculate similarity
                    .do()
                )
                
                products = result.get('data', {}).get('Get', {}).get('Product', [])
                print(f"[WEAVIATE] Retrieved {len(products)} products for similarity calculation")
                
                # Calculate similarity and sort
                scored_products = []
                for product in products:
                    if product.get('image_embedding'):
                        similarity = self._cosine_similarity(query_embedding, product['image_embedding'])
                        product['similarity'] = similarity
                        product['_additional'] = {'distance': 1 - similarity}  # Convert to distance
                        scored_products.append(product)
                
                # Sort by similarity (highest first)
                scored_products.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                
                # Return top results
                results = scored_products[:limit]
                print(f"[WEAVIATE] Image search returned {len(results)} results")
                if results:
                    print(f"[WEAVIATE] Best match: {results[0].get('title', 'Unknown')} (similarity: {results[0].get('similarity', 0):.3f})")
                
                return results
            else:
                print(f"[WEAVIATE] OpenAI not configured, using fallback")
                return self._fallback_image_search(limit)
                
        except Exception as e:
            print(f"[WEAVIATE] Error in image search: {e}")
            import traceback
            print(f"[WEAVIATE] Full traceback: {traceback.format_exc()}")
            return self._fallback_image_search(limit)
    
    def _fallback_image_search(self, limit: int) -> List[Dict]:
        """Fallback image search - return all products"""
        try:
            result = (
                self.client.query
                .get("Product", ["product_id", "title", "description", "price", "image_url", "vendor", "product_type"])
                .with_limit(limit)
                .do()
            )
            
            products = result.get('data', {}).get('Get', {}).get('Product', [])
            print(f"[WEAVIATE] Image search fallback returned {len(products)} products")
            return products
        except Exception as e:
            print(f"[WEAVIATE] Error in image search fallback: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            print(f"[WEAVIATE] Error calculating similarity: {e}")
            return 0
    
    def search_by_text_and_image(self, query: str, image_base64: str, limit: int = 10) -> List[Dict]:
        """Search products by both text and image using hybrid search"""
        try:
            print(f"[WEAVIATE] Attempting combined text+image search for query: '{query}' with image")
            print(f"[WEAVIATE] Image vectorization not supported with {self.vectorizer}, prioritizing text search")
            
            # Since image search isn't supported, prioritize text search
            if query:
                print(f"[WEAVIATE] Using text search as primary method")
                text_results = self.search_by_text(query, limit)
                print(f"[WEAVIATE] Text search returned {len(text_results)} results")
                return text_results
            else:
                print(f"[WEAVIATE] No query provided, falling back to image search")
                image_results = self.search_by_image(image_base64, limit)
                print(f"[WEAVIATE] Image search fallback returned {len(image_results)} results")
                return image_results
            
        except Exception as e:
            print(f"[WEAVIATE] Error in combined search: {e}")
            import traceback
            print(f"[WEAVIATE] Full traceback: {traceback.format_exc()}")
            return []
    
    def _download_and_encode_image(self, image_url: str) -> Optional[str]:
        """Download image from URL and encode to base64"""
        try:
            # Handle relative URLs - try local file system first
            if image_url.startswith('/'):
                # Try to read from local file system
                local_path = f".{image_url}"  # Convert /uploads/... to ./uploads/...
                print(f"[WEAVIATE] Trying local file: {local_path}")
                
                if os.path.exists(local_path):
                    with open(local_path, 'rb') as f:
                        image_data = f.read()
                    print(f"[WEAVIATE] Read image from local file: {len(image_data)} bytes")
                else:
                    # Fall back to HTTP request
                    image_url = f"http://localhost:5000{image_url}"
                    print(f"[WEAVIATE] Local file not found, trying HTTP: {image_url}")
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        image_data = response.content
                    else:
                        print(f"[WEAVIATE] HTTP request failed: {response.status_code}")
                        return None
            else:
                print(f"[WEAVIATE] Downloading image from: {image_url}")
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image_data = response.content
                else:
                    print(f"[WEAVIATE] Download failed: {response.status_code}")
                    return None
            
            # Process the image data
            img = Image.open(io.BytesIO(image_data))
            
            # Resize if larger than 1024px in any dimension
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            
            # Encode to base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error downloading/encoding image: {e}")
        
        return None
    
    def encode_image_file(self, image_file) -> Optional[str]:
        """Encode uploaded image file to base64"""
        try:
            img = Image.open(image_file)
            
            # Resize if larger than 1024px
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            
            # Encode to base64
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image file: {e}")
            return None