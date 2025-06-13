"""
OpenAI Service for Image and Text Embeddings
"""
import os
import base64
import requests
from typing import List, Optional, Dict
import json
from PIL import Image
import io

class OpenAIService:
    def __init__(self, api_key: str = None):
        """Initialize OpenAI service with API key"""
        self.api_key = api_key or self._get_config_api_key() or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            print("[OPENAI] Warning: No API key provided")
        
        self.base_url = "https://api.openai.com/v1"
        
    def _get_config_api_key(self):
        """Get OpenAI API key from database config"""
        try:
            from database import db
            from sqlalchemy import text
            
            # Check if config table exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_config'"))
            if not result.fetchone():
                return None
            
            # Get the latest config
            config = db.session.execute(text("SELECT openai_api_key FROM vector_config ORDER BY id DESC LIMIT 1")).fetchone()
            if config and config[0]:
                return config[0]
                
        except Exception as e:
            print(f"[OPENAI] Error getting API key from config: {e}")
        
        return None
    
    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.api_key)
    
    def get_text_embedding(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """Generate text embedding using OpenAI"""
        if not self.api_key:
            print("[OPENAI] No API key available for text embedding")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "input": text,
                "model": model
            }
            
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                print(f"[OPENAI] Text embedding failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[OPENAI] Error generating text embedding: {e}")
            return None
    
    def get_image_embedding(self, image_base64: str, model: str = "clip-vit-base-patch32") -> Optional[List[float]]:
        """Generate image embedding using OpenAI Vision"""
        if not self.api_key:
            print("[OPENAI] No API key available for image embedding")
            return None
        
        # For now, we'll use a vision-based approach with GPT-4V to describe the image
        # and then get text embeddings of that description
        try:
            # First, get image description using GPT-4V
            description = self.describe_image(image_base64)
            if not description:
                return None
            
            # Then get text embedding of the description
            return self.get_text_embedding(description)
            
        except Exception as e:
            print(f"[OPENAI] Error generating image embedding: {e}")
            return None
    
    def describe_image(self, image_base64: str) -> Optional[str]:
        """Generate description of image using GPT-4V"""
        if not self.api_key:
            print("[OPENAI] No API key available for image description")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Ensure the base64 data has proper prefix
            if not image_base64.startswith('data:image'):
                image_base64 = f"data:image/jpeg;base64,{image_base64}"
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this product image in detail, focusing on: 1) Type of product, 2) Color and style, 3) Key features and characteristics, 4) Material or texture if visible, 5) Overall appearance. Be concise but descriptive for search purposes."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_base64
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                description = result['choices'][0]['message']['content']
                print(f"[OPENAI] Generated image description: {description[:100]}...")
                return description
            else:
                print(f"[OPENAI] Image description failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[OPENAI] Error describing image: {e}")
            return None
    
    def search_images_by_text(self, query: str, image_descriptions: List[Dict]) -> List[Dict]:
        """Search images using text query against image descriptions"""
        if not self.api_key or not image_descriptions:
            return []
        
        try:
            # Get embedding for search query
            query_embedding = self.get_text_embedding(query)
            if not query_embedding:
                return []
            
            # Calculate similarity with each image description
            results = []
            for item in image_descriptions:
                if 'embedding' in item and item['embedding']:
                    similarity = self._cosine_similarity(query_embedding, item['embedding'])
                    item['similarity'] = similarity
                    results.append(item)
            
            # Sort by similarity
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            return results
            
        except Exception as e:
            print(f"[OPENAI] Error in image search: {e}")
            return []
    
    def search_images_by_image(self, query_image_base64: str, image_descriptions: List[Dict]) -> List[Dict]:
        """Search images using image query against stored image descriptions"""
        if not self.api_key or not image_descriptions:
            return []
        
        try:
            # Get embedding for query image
            query_embedding = self.get_image_embedding(query_image_base64)
            if not query_embedding:
                return []
            
            # Calculate similarity with each stored image
            results = []
            for item in image_descriptions:
                if 'embedding' in item and item['embedding']:
                    similarity = self._cosine_similarity(query_embedding, item['embedding'])
                    item['similarity'] = similarity
                    results.append(item)
            
            # Sort by similarity
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            return results
            
        except Exception as e:
            print(f"[OPENAI] Error in image-to-image search: {e}")
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
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            print(f"[OPENAI] Error calculating similarity: {e}")
            return 0
    
    def process_image_for_embedding(self, image_base64: str) -> Optional[Dict]:
        """Process an image to generate both description and embedding"""
        if not self.api_key:
            return None
        
        try:
            # Generate description
            description = self.describe_image(image_base64)
            if not description:
                return None
            
            # Generate embedding from description
            embedding = self.get_text_embedding(description)
            if not embedding:
                return None
            
            return {
                'description': description,
                'embedding': embedding,
                'embedding_model': 'text-embedding-3-small',
                'description_model': 'gpt-4o-mini'
            }
            
        except Exception as e:
            print(f"[OPENAI] Error processing image: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """Test OpenAI API connection"""
        if not self.api_key:
            return {
                'connected': False,
                'error': 'No API key provided'
            }
        
        try:
            # Test with a simple embedding request
            embedding = self.get_text_embedding("test")
            
            if embedding:
                return {
                    'connected': True,
                    'embedding_dimensions': len(embedding),
                    'message': 'OpenAI API connection successful'
                }
            else:
                return {
                    'connected': False,
                    'error': 'Failed to generate test embedding'
                }
                
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }