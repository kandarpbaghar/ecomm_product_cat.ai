"""
Shopping Agent Implementation using Google ADK
Provides conversational shopping assistance with product search and recommendations
"""

import json
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
import base64

from .llm_providers import LLMProviderFactory, BaseLLMProvider
from .conversation import ConversationManager
from .prompts import SYSTEM_PROMPTS


def search_products_by_text(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search for products using natural language query"""
    try:
        # Import here to avoid circular imports
        from services.weaviate_service import WeaviateService
        
        print(f"[AGENT SEARCH] Searching for: {query}")
        weaviate_service = WeaviateService()
        results = weaviate_service.search_by_text(query, limit=limit)
        print(f"[AGENT SEARCH] Found {len(results)} results")
        print(f"[AGENT SEARCH] Sample result: {results[0] if results else 'No results'}")
        
        # Convert results to expected format for frontend
        formatted_products = []
        for result in results:
            formatted_product = {
                "id": result.get("product_id"),  # Changed from "id" to "product_id"
                "title": result.get("title"),
                "description": result.get("description"),
                "price": result.get("price"),
                "vendor": result.get("vendor"),
                "quantity": result.get("quantity", 0),
                # Convert image format for frontend
                "images": []
            }
            
            # Handle different image formats from Weaviate
            if result.get("image_url"):
                formatted_product["images"] = [{"url": result["image_url"]}]
            elif result.get("images"):
                if isinstance(result["images"], list):
                    formatted_product["images"] = [{"url": img} for img in result["images"]]
                else:
                    formatted_product["images"] = [{"url": result["images"]}]
            
            formatted_products.append(formatted_product)
        
        return {
            "success": True,
            "products": formatted_products,
            "count": len(formatted_products)
        }
    except Exception as e:
        print(f"[AGENT SEARCH] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


def search_products_by_image(image_base64: str, limit: int = 10) -> Dict[str, Any]:
    """Search for similar products using an image"""
    try:
        from services.weaviate_service import WeaviateService
        
        weaviate_service = WeaviateService()
        results = weaviate_service.search_by_image(image_base64, limit=limit)
        
        # Convert results to expected format for frontend (same as text search)
        formatted_products = []
        for result in results:
            formatted_product = {
                "id": result.get("product_id"),  # Use product_id as id
                "title": result.get("title"),
                "description": result.get("description"),
                "price": result.get("price"),
                "vendor": result.get("vendor"),
                "quantity": result.get("quantity", 0),
                # Convert image format for frontend
                "images": []
            }
            
            # Handle different image formats from Weaviate
            if result.get("image_url"):
                formatted_product["images"] = [{"url": result["image_url"]}]
            elif result.get("images"):
                if isinstance(result["images"], list):
                    formatted_product["images"] = [{"url": img} for img in result["images"]]
                else:
                    formatted_product["images"] = [{"url": result["images"]}]
            
            formatted_products.append(formatted_product)
        
        return {
            "success": True,
            "products": formatted_products,
            "count": len(formatted_products)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


def get_product_details(product_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific product"""
    try:
        from models.sku import SKU
        
        product = SKU.query.get(product_id)
        if not product:
            return {
                "success": False,
                "error": "Product not found"
            }
        
        return {
            "success": True,
            "product": {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": float(product.price) if product.price else None,
                "vendor": product.vendor,
                "quantity": product.quantity,
                "images": [{"url": img.url} for img in product.images] if product.images else []
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def filter_products(categories: List[int] = None, vendors: List[str] = None, 
                   min_price: float = None, max_price: float = None, 
                   in_stock: bool = True, limit: int = 20) -> Dict[str, Any]:
    """Filter products by various criteria"""
    try:
        from models.sku import SKU
        from sqlalchemy import and_
        
        query = SKU.query
        
        filters = []
        
        if categories:
            filters.append(SKU.category_id.in_(categories))
        
        if vendors:
            filters.append(SKU.vendor.in_(vendors))
        
        if min_price is not None:
            filters.append(SKU.price >= min_price)
        
        if max_price is not None:
            filters.append(SKU.price <= max_price)
        
        if in_stock:
            filters.append(SKU.quantity > 0)
        
        if filters:
            query = query.filter(and_(*filters))
        
        products = query.limit(limit).all()
        
        return {
            "success": True,
            "products": [{
                "id": p.id,
                "title": p.title,
                "price": float(p.price) if p.price else None,
                "vendor": p.vendor,
                "quantity": p.quantity,
                "images": [{"url": img.url} for img in p.images] if p.images else []
            } for p in products],
            "count": len(products)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


def get_similar_products(product_id: int, limit: int = 5) -> Dict[str, Any]:
    """Find products similar to a given product"""
    try:
        from models.sku import SKU
        
        # Get the reference product
        product = SKU.query.get(product_id)
        if not product:
            return {
                "success": False,
                "error": "Product not found",
                "products": []
            }
        
        # Use text search with the product title to find similar items
        from services.weaviate_service import WeaviateService
        weaviate_service = WeaviateService()
        results = weaviate_service.search_by_text(product.title, limit=limit+1)  # +1 to exclude the original
        
        # Remove the original product from results
        filtered_results = [p for p in results if p.get('id') != product_id][:limit]
        
        return {
            "success": True,
            "products": filtered_results,
            "count": len(filtered_results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


class ShoppingAgent:
    """AI Shopping Assistant Agent using Google ADK"""
    
    def __init__(self, model: str = "gemini-2.0-flash", **kwargs):
        self.model = model
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 500)
        self.conversation_manager = ConversationManager()  # Keep for backward compatibility
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Initialize the Google ADK agent with tools"""
        self.agent = Agent(
            name="shopping_assistant",
            model=self.model,
            description="AI assistant for product search and shopping help",
            instruction="""You are an intelligent shopping assistant. You help users find products by understanding their intent and using the appropriate tools.

IMPORTANT INSTRUCTIONS:
1. When users ask for products, analyze their request carefully and use the right tool:
   - For basic search: use search_products_by_text with relevant keywords
   - For filtering by price/category: use filter_products with specific parameters
   - For image search: use search_products_by_image
   - For similar products: use get_similar_products

2. Maintain conversation context:
   - Remember what product types the user was looking for
   - If they say "how about below $550" after asking for shirts, continue looking for shirts
   - Use context from previous messages to understand follow-up requests

3. Extract filters intelligently:
   - Product types: shirts, pants, shoes, etc.
   - Price ranges: below/under/less than X, above/over/more than X
   - Other criteria: brands, colors, etc.

4. Always provide helpful responses and suggest alternatives if no products are found.

Available tools:
- search_products_by_text(query, limit): Search products by text
- search_products_by_image(image_base64, limit): Search by image similarity  
- filter_products(categories, vendors, min_price, max_price, in_stock, limit): Filter with specific criteria
- get_product_details(product_id): Get detailed product info
- get_similar_products(product_id, limit): Find similar products""",
            tools=[
                search_products_by_text,
                search_products_by_image,
                get_product_details,
                filter_products,
                get_similar_products
            ]
        )
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        image_data: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message using Google ADK's intelligent agent system
        """
        try:
            print(f"ShoppingAgent.process_message called with: {message}")
            
            # Get conversation history for context
            history = self.conversation_manager.get_history(session_id)
            
            # Build context-aware message for the LLM
            if len(history) > 0:
                # Add conversation context
                context_message = f"Previous conversation context:\n"
                for msg in history[-3:]:  # Last 3 messages for context
                    context_message += f"{msg['role']}: {msg['content']}\n"
                context_message += f"\nUser: {message}"
                full_message = context_message
            else:
                full_message = message
            
            if image_data:
                full_message = f"[Image provided] {full_message}"
            
            print(f"[AGENT] Full context message: {full_message}")
            
            # Implement intelligent tool selection using LLM reasoning
            tool_choice, params = await self._analyze_intent_and_choose_tool(full_message, session_id)
            print(f"[AGENT] Tool choice: {tool_choice}, Params: {params}")
            
            # Handle image data for image search
            if tool_choice == "search_products_by_image":
                if image_data:
                    params["image_base64"] = image_data
                elif params.get("image_base64") == "provided_in_context" and not image_data:
                    # LLM thinks this should be image search but no image provided
                    # This is likely a follow-up query - convert to filter_products instead
                    print("[AGENT] LLM wanted image search but no image provided - converting to filter_products")
                    tool_choice = "filter_products"
                    params.pop("image_base64", None)
                    params.pop("apply_price_filter", None)
                    params["in_stock"] = False
                    
                    # For follow-up queries, try to infer product type from context
                    if not params.get("product_types_filter"):
                        # Get conversation history to extract product types from previous searches
                        try:
                            history = self.conversation_manager.get_history(session_id)
                            for msg in reversed(history[-6:]):  # Check last 6 messages
                                if msg.get('role') == 'assistant':
                                    # First check metadata for explicit product types
                                    metadata = msg.get('metadata', {})
                                    if metadata.get('product_types'):
                                        params["product_types_filter"] = metadata['product_types']
                                        print(f"[AGENT] Using product types from metadata: {metadata['product_types']}")
                                        break
                                    
                                    # Fallback to content analysis
                                    content = msg.get('content', '').lower()
                                    if 'pant' in content and ('cotton' in content or 'khaki' in content or 'trouser' in content):
                                        params["product_types_filter"] = ["pants"]
                                        print(f"[AGENT] Inferred product type 'pants' from content")
                                        break
                                    elif 'shirt' in content and ('sleeve' in content or 'cotton' in content or 'blouse' in content):
                                        params["product_types_filter"] = ["shirt"]
                                        print(f"[AGENT] Inferred product type 'shirt' from content")
                                        break
                                    elif 'shoe' in content or 'sneaker' in content or 'boot' in content:
                                        params["product_types_filter"] = ["shoes"]
                                        print(f"[AGENT] Inferred product type 'shoes' from content")
                                        break
                        except Exception as e:
                            print(f"[AGENT] Error extracting context: {e}")
                            pass
            
            # Execute the chosen tool
            if tool_choice == "filter_products":
                # Remove product_types_filter from params before calling filter_products
                product_types_filter = params.pop("product_types_filter", None)
                
                # Clean params to only include valid filter_products parameters
                valid_params = {
                    "categories": params.get("categories"),
                    "vendors": params.get("vendors"),
                    "min_price": params.get("min_price"),
                    "max_price": params.get("max_price"),
                    "in_stock": params.get("in_stock", False),
                    "limit": params.get("limit", 20)
                }
                # Remove None values
                valid_params = {k: v for k, v in valid_params.items() if v is not None}
                
                result = filter_products(**valid_params)
                products = result.get('products', []) if result.get('success') else []
                
                # Post-process for product type filtering if needed
                if product_types_filter and products:
                    original_count = len(products)
                    filtered_products = []
                    for product in products:
                        title_lower = product.get('title', '').lower()
                        # Check if the product title contains any of the product types
                        product_type_keywords = {
                            "shirt": ["shirt", "blouse", "top", "tee", "t-shirt", "tshirt"],
                            "pants": ["pant", "pants", "jean", "jeans", "trouser", "trousers", "slack", "slacks", "legging", "leggings"],
                            "shoes": ["shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "sandal", "sandals", "heel", "heels"],
                            "dress": ["dress", "dresses", "gown", "frock"],
                            "jacket": ["jacket", "coat", "blazer", "hoodie", "cardigan", "sweater"]
                        }
                        
                        # Check if product matches ANY of the requested product types
                        matches_any_type = False
                        for product_type in product_types_filter:
                            keywords = product_type_keywords.get(product_type, [product_type])
                            if any(keyword in title_lower for keyword in keywords):
                                matches_any_type = True
                                break
                        
                        if matches_any_type:
                            filtered_products.append(product)
                    
                    products = filtered_products
                    print(f"[AGENT] Filtered {original_count} products down to {len(products)} for product types {product_types_filter}")
                
                if products:
                    filter_desc = []
                    if params.get('categories'): filter_desc.append("categories")
                    if params.get('min_price'): filter_desc.append(f"price above ${params['min_price']}")
                    if params.get('max_price'): filter_desc.append(f"price below ${params['max_price']}")
                    if params.get('vendors'): filter_desc.append(f"vendors: {', '.join(params['vendors'])}")
                    if product_types_filter: 
                        if len(product_types_filter) == 1:
                            filter_desc.append(f"product type: {product_types_filter[0]}")
                        else:
                            filter_desc.append(f"product types: {' and '.join(product_types_filter)}")
                    
                    response_text = f"I found {len(products)} products" + (f" with {', '.join(filter_desc)}" if filter_desc else "") + ". Here are some great options:"
                else:
                    response_text = "I couldn't find any products matching your criteria. Try adjusting your filters."
                    
            elif tool_choice == "search_products_by_text":
                result = search_products_by_text(params['query'], params.get('limit', 10))
                products = result.get('products', []) if result.get('success') else []
                
                if products:
                    response_text = f"I found {len(products)} products for '{params['query']}'. Here are some great options:"
                else:
                    response_text = f"I couldn't find any products for '{params['query']}'. Try a different search term."
                    
            elif tool_choice == "search_products_by_image":
                result = search_products_by_image(params['image_base64'], params.get('limit', 20))
                products = result.get('products', []) if result.get('success') else []
                
                # Apply price filters if specified
                if params.get('apply_price_filter') and products:
                    min_price = params.get('min_price')
                    max_price = params.get('max_price')
                    
                    if min_price is not None or max_price is not None:
                        filtered_products = []
                        for product in products:
                            price = product.get('price')
                            if price is not None:
                                try:
                                    price_val = float(price)
                                    if min_price is not None and price_val < min_price:
                                        continue
                                    if max_price is not None and price_val > max_price:
                                        continue
                                    filtered_products.append(product)
                                except (ValueError, TypeError):
                                    continue
                        
                        products = filtered_products
                        print(f"[AGENT] Applied price filter: {len(result.get('products', []))} -> {len(products)} products")
                
                if products:
                    filter_desc = ""
                    if params.get('min_price'): filter_desc += f" above ${params['min_price']}"
                    if params.get('max_price'): filter_desc += f" below ${params['max_price']}"
                    
                    response_text = f"I found {len(products)} similar products based on your image"
                    if filter_desc:
                        response_text += f" with prices{filter_desc}"
                    response_text += ". Here are some great options:"
                else:
                    response_text = "I couldn't find similar products for your image that match your criteria. Try adjusting your filters."
                    
            else:
                # Default to basic search
                result = search_products_by_text(message, limit=10)
                products = result.get('products', []) if result.get('success') else []
                response_text = f"I found {len(products)} products for you." if products else "I couldn't find any products matching your request."
            
            print(f"[AGENT] Final response: {response_text}")
            print(f"[AGENT] Products found: {len(products)}")
            
            # Extract product types from results for context
            detected_product_types = []
            if products:
                for product in products[:3]:  # Check first 3 products
                    title_lower = product.get('title', '').lower()
                    if any(word in title_lower for word in ['pant', 'jean', 'trouser', 'slack', 'legging']):
                        if 'pants' not in detected_product_types:
                            detected_product_types.append('pants')
                    elif any(word in title_lower for word in ['shirt', 'blouse', 'top', 'tee']):
                        if 'shirt' not in detected_product_types:
                            detected_product_types.append('shirt')
                    elif any(word in title_lower for word in ['shoe', 'sneaker', 'boot', 'sandal']):
                        if 'shoes' not in detected_product_types:
                            detected_product_types.append('shoes')
            
            # Save to conversation history
            self.conversation_manager.add_message(
                session_id, 
                "user", 
                message,
                metadata={"has_image": bool(image_data)}
            )
            self.conversation_manager.add_message(
                session_id,
                "assistant",
                response_text,
                metadata={
                    "products_shown": len(products),
                    "product_types": detected_product_types,
                    "tool_used": tool_choice
                }
            )
            
            return {
                "success": True,
                "response": response_text,
                "products": products,
                "session_id": session_id,
                "suggestions": self._generate_suggestions(None, products)
            }
            
        except Exception as e:
            print(f"[AGENT] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error. Please try again.",
                "products": []
            }
    
    def _generate_suggestions(self, response: Any, products: List[Dict]) -> List[str]:
        """Generate follow-up suggestions based on the conversation"""
        suggestions = []
        
        if products:
            suggestions.extend([
                "Show me similar products",
                "Filter by price range",
                "Compare these products"
            ])
        else:
            suggestions.extend([
                "I'm looking for running shoes",
                "Show me products under $100",
                "What's popular right now?"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def get_product_recommendations(
        self,
        session_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get personalized product recommendations"""
        try:
            # Get user context from conversation history
            history = self.conversation_manager.get_history(session_id)
            
            # Extract preferences from conversation
            extracted_prefs = self._extract_preferences(history)
            
            # Merge with provided preferences
            all_preferences = {**extracted_prefs, **(preferences or {})}
            
            # Generate recommendations using filter_products tool
            response = await self.agent.generate(
                f"Generate product recommendations based on these preferences: {all_preferences}"
            )
            
            return {
                "success": True,
                "recommendations": [],
                "preferences_used": all_preferences
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    def _extract_preferences(self, history: List[Dict]) -> Dict[str, Any]:
        """Extract user preferences from conversation history"""
        preferences = {}
        
        # Simple extraction logic (can be enhanced with NLP)
        for msg in history:
            if msg.get("role") == "user":
                content_lower = msg.get("content", "").lower()
                
                # Extract price preferences
                if "under $" in content_lower or "less than $" in content_lower:
                    # Extract price value (simplified)
                    import re
                    price_match = re.search(r'\$(\d+)', msg.get("content", ""))
                    if price_match:
                        preferences['price_range'] = {'max': float(price_match.group(1))}
                
                # Extract category preferences
                categories_keywords = {
                    'shoes': [1, 2],  # Shoe category IDs
                    'clothing': [3, 4],  # Clothing category IDs
                    'electronics': [5, 6]  # Electronics category IDs
                }
                
                for keyword, cat_ids in categories_keywords.items():
                    if keyword in content_lower:
                        preferences.setdefault('categories', []).extend(cat_ids)
        
        return preferences
    
    async def _analyze_intent_and_choose_tool(self, full_message: str, session_id: str = None) -> tuple:
        """
        Hybrid approach: Use rule-based for simple cases, LLM for complex queries
        """
        try:
            message_lower = full_message.lower()
            
            # FAST PATH: Simple image search (only if no additional filters/text)
            if "[image provided]" in message_lower:
                # Extract the text part (remove "[Image provided]")
                text_part = message_lower.replace("[image provided]", "").strip()
                
                # If there's meaningful text with the image, use LLM for complex analysis
                if text_part and len(text_part) > 0:
                    # Check if text contains price filters, specific requests, etc.
                    has_price_filter = any(word in text_part for word in ["below", "under", "above", "over", "less", "more", "$"])
                    has_specific_request = any(word in text_part for word in ["similar", "like", "color", "brand", "style", "cheaper", "expensive"])
                    
                    if has_price_filter or has_specific_request:
                        # Use LLM to handle complex image + text query
                        return await self._llm_analyze_intent(full_message, session_id)
                
                # Simple image-only search
                return "search_products_by_image", {
                    "image_base64": "provided_in_context",
                    "limit": 10
                }
            
            # FAST PATH: Simple product search (single product type, no filters)
            import re
            simple_product_match = re.match(r"^(?:show me|find|search for|i want|looking for)\s+(\w+)s?$", message_lower.strip())
            if simple_product_match:
                product = simple_product_match.group(1)
                return "search_products_by_text", {
                    "query": product,
                    "limit": 20
                }
            
            # FAST PATH: Simple price filter
            simple_price_below = re.match(r"^(?:show me|find)\s+(?:products|items)?\s*(?:under|below|less than)\s*\$?(\d+)$", message_lower.strip())
            if simple_price_below:
                return "filter_products", {
                    "max_price": float(simple_price_below.group(1)),
                    "limit": 20,
                    "in_stock": False
                }
            
            # COMPLEX QUERIES: Use LLM for context understanding
            # This includes follow-ups, multiple filters, contextual references
            return await self._llm_analyze_intent(full_message, session_id)
            
        except Exception as e:
            print(f"[AGENT] Error in intent analysis: {e}")
            # Fallback to simple text search
            return "search_products_by_text", {
                "query": full_message.strip(),
                "limit": 20
            }
    
    async def _llm_analyze_intent(self, full_message: str, session_id: str = None) -> tuple:
        """
        Use LLM to analyze complex queries with context
        """
        try:
            # Get conversation history if available
            history_context = ""
            had_previous_image_search = False
            
            if session_id and hasattr(self, 'conversation_manager'):
                history = self.conversation_manager.get_history(session_id)
                if history:
                    # Include last 3 exchanges for context
                    recent_history = history[-6:]  # 3 user + 3 assistant messages
                    history_context = "Previous conversation:\n"
                    for msg in recent_history:
                        history_context += f"{msg['role']}: {msg['content'][:200]}...\n"
                        # Check if previous messages involved image searches
                        if msg.get('role') == 'user' and 'image' in msg.get('content', '').lower():
                            had_previous_image_search = True
                        elif msg.get('role') == 'assistant' and 'image' in msg.get('content', '').lower():
                            had_previous_image_search = True
            
            # Add context about previous image searches
            if had_previous_image_search and "[image provided]" not in full_message.lower():
                history_context += "\nNOTE: Previous messages involved image searches. For follow-up queries without new images, use filter_products to refine the results."
            
            # Create prompt for LLM
            analysis_prompt = f"""Analyze this shopping query and return a JSON response.

{history_context}

Current query: {full_message}

Determine:
1. What products the user is looking for (use context if this is a follow-up)
2. Any price constraints (min_price, max_price)
3. Any vendor/brand preferences
4. Which tool to use

Available tools:
- search_products_by_text: For general product searches
- search_products_by_image: For image-based searches (use when image is provided)
- filter_products: When specific price/vendor filters are needed
- get_product_details: For specific product ID
- get_similar_products: For finding similar items

IMPORTANT: 
- If "[Image provided]" is in the query, use search_products_by_image with any price filters
- If NO image is provided but the previous conversation had image searches, use filter_products to filter by the new criteria
- For follow-up queries without images (like "anything below 500?"), use filter_products NOT search_products_by_image

Return ONLY valid JSON in this format:
{{
    "tool": "tool_name",
    "params": {{
        "query": "search query (only for search_products_by_text)",
        "min_price": null or number,
        "max_price": null or number,
        "vendors": [] or ["vendor1", "vendor2"],
        "product_types_filter": [] or ["shirt", "pants", etc],
        "limit": 20,
        "image_base64": "provided_in_context" (only for search_products_by_image),
        "apply_price_filter": true (only for search_products_by_image with price filters)
    }},
    "reasoning": "brief explanation"
}}

IMPORTANT: Only include relevant parameters for each tool:
- search_products_by_text: query, limit
- search_products_by_image: image_base64, limit, apply_price_filter, min_price, max_price (if filtering)
- filter_products: min_price, max_price, vendors, product_types_filter, limit"""

            # Get LLM provider configuration from database
            llm_provider = "openai"  # default
            llm_model = "gpt-4-turbo-preview"  # default
            api_key = None
            
            try:
                from models.agent import AgentConfig
                config = AgentConfig.get_current_config()
                if config:
                    llm_provider = config.llm_provider or "openai"
                    llm_model = config.llm_model or "gpt-4-turbo-preview"
                    
                    # Get the appropriate API key based on provider
                    if llm_provider.lower() == "openai":
                        api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
                    elif llm_provider.lower() == "anthropic":
                        api_key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
                    elif llm_provider.lower() == "google":
                        api_key = config.google_api_key or os.getenv("GOOGLE_API_KEY")
            except Exception as e:
                print(f"[AGENT] Error getting config: {e}")
                # Fallback to environment variables
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                print(f"[AGENT] No API key found for provider '{llm_provider}', falling back to rule-based analysis")
                return self._fallback_rule_based_analysis(full_message)
            
            # Use LLM to analyze
            provider = LLMProviderFactory.create_provider(llm_provider, api_key)
            messages = [{"role": "user", "content": analysis_prompt}]
            
            # Use appropriate model for the provider
            if llm_provider.lower() == "openai":
                model = "gpt-3.5-turbo"  # Fast model for analysis
            elif llm_provider.lower() == "anthropic":
                model = "claude-3-haiku-20240307"  # Fast model for analysis
            else:  # google
                model = "gemini-1.5-flash"  # Fast model for analysis
            
            response = provider.chat_completion(
                messages=messages,
                model=model,
                temperature=0.1,  # Low temp for consistent JSON
                max_tokens=300
            )
            
            # Parse LLM response
            response_text = response.content.strip()
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            print(f"[AGENT] LLM Analysis: {result.get('reasoning', 'No reasoning provided')}")
            
            # Validate and clean params
            tool = result.get("tool", "search_products_by_text")
            params = result.get("params", {})
            
            # Ensure required params based on tool
            if tool == "filter_products":
                params["in_stock"] = params.get("in_stock", False)
                params["limit"] = params.get("limit", 30)
            elif tool == "search_products_by_text":
                if not params.get("query"):
                    params["query"] = full_message.strip()
                params["limit"] = params.get("limit", 20)
            
            return tool, params
            
        except Exception as e:
            print(f"[AGENT] LLM analysis failed: {e}")
            # Fallback to rule-based extraction
            return self._fallback_rule_based_analysis(full_message)
    
    def _fallback_rule_based_analysis(self, full_message: str) -> tuple:
        """
        Fallback rule-based analysis when LLM fails
        """
        message_lower = full_message.lower()
        
        # Check if this is an image query first
        if "[image provided]" in message_lower:
            # Extract the text part
            text_part = message_lower.replace("[image provided]", "").strip()
            
            # Extract price filters from text
            import re
            min_price = None
            max_price = None
            
            above_match = re.search(r'(?:above|over|more than)\s*\$?(\d+)', text_part)
            below_match = re.search(r'(?:below|under|less than)\s*\$?(\d+)', text_part)
            
            if above_match:
                min_price = float(above_match.group(1))
            if below_match:
                max_price = float(below_match.group(1))
            
            # Return image search with price filters
            params = {
                "image_base64": "provided_in_context",
                "limit": 20
            }
            
            if min_price or max_price:
                params["apply_price_filter"] = True
                if min_price:
                    params["min_price"] = min_price
                if max_price:
                    params["max_price"] = max_price
            
            return "search_products_by_image", params
        
        # Regular text-based analysis
        # Extract price filters
        import re
        min_price = None
        max_price = None
        
        # Price patterns
        above_match = re.search(r'(?:above|over|more than)\s*\$?(\d+)', message_lower)
        below_match = re.search(r'(?:below|under|less than)\s*\$?(\d+)', message_lower)
        
        if above_match:
            min_price = float(above_match.group(1))
        if below_match:
            max_price = float(below_match.group(1))
        
        # Extract product types
        product_types = []
        product_keywords = {
            "shirt": ["shirt", "blouse", "top", "tee"],
            "pants": ["pant", "jean", "trouser", "slack", "legging"],
            "shoes": ["shoe", "sneaker", "boot", "sandal", "heel"],
            "dress": ["dress", "gown", "frock"],
            "jacket": ["jacket", "coat", "blazer", "hoodie", "sweater"]
        }
        
        for product_type, keywords in product_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                product_types.append(product_type)
        
        # Decide tool based on extracted info
        if min_price or max_price:
            return "filter_products", {
                "min_price": min_price,
                "max_price": max_price,
                "product_types_filter": product_types,
                "limit": 30,
                "in_stock": False
            }
        elif product_types:
            return "search_products_by_text", {
                "query": " ".join(product_types),
                "limit": 20
            }
        else:
            # Default text search
            return "search_products_by_text", {
                "query": full_message.strip(),
                "limit": 20
            }
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        self.conversation_manager.clear_history(session_id)
    
    async def _get_or_create_session(self, session_id: str):
        """Get or create an ADK session"""
        try:
            # Try to get existing session
            session = await self.session_service.get_session(session_id)
            if session:
                return session
        except:
            pass
        
        # Create new session with initial state
        session = await self.session_service.create_session(
            app_name="shopping_assistant",
            user_id=session_id,
            state={
                "app:conversation_count": 0,
                "app:last_product_type": None,
                "app:last_price_range": None,
                "app:last_search_results": [],
                "app:user_preferences": {},
                "app:conversation_theme": "shopping"
            }
        )
        return session
    
    def _analyze_session_context(self, session, current_message: str) -> Dict[str, Any]:
        """Analyze session state to understand context"""
        state = session.state
        context_info = {
            "is_first_message": state.get("app:conversation_count", 0) == 0,
            "previous_searches": state.get("app:previous_searches", []),
            "last_product_type": state.get("app:last_product_type"),
            "last_price_range": state.get("app:last_price_range"),
            "conversation_theme": state.get("app:conversation_theme", "shopping"),
            "follow_up_intent": None,
            "user_preferences": state.get("app:user_preferences", {})
        }
        
        # Analyze current message for follow-up intent
        current_lower = current_message.lower()
        follow_up_phrases = [
            "show me more", "similar", "like these", "other options", 
            "different", "cheaper", "expensive", "better", "other colors"
        ]
        
        for phrase in follow_up_phrases:
            if phrase in current_lower:
                context_info["follow_up_intent"] = phrase
                break
        
        # Check for referential phrases
        referential_phrases = ["these", "those", "the last ones", "previous", "earlier"]
        context_info["has_reference"] = any(phrase in current_lower for phrase in referential_phrases)
        
        return context_info
    
    async def _update_session_state(self, session, updates: Dict[str, Any]):
        """Update session state with new information"""
        # For InMemorySessionService, we can directly update the session state
        # since it's stored in memory and the session object is a reference
        for key, value in updates.items():
            session.state[f"app:{key}"] = value
        
        # Note: For production, you would use proper ADK event system
        # but InMemorySessionService allows direct state modification
    
    def _analyze_conversation_context(self, history: List[Dict], context: Dict, current_message: str) -> Dict[str, Any]:
        """Analyze conversation history to understand context"""
        context_info = {
            "is_first_message": len(history) == 0,
            "previous_searches": [],
            "last_product_type": None,
            "last_price_range": None,
            "conversation_theme": None,
            "follow_up_intent": None
        }
        
        # Analyze previous messages
        for msg in history[-5:]:  # Look at last 5 messages
            if msg["role"] == "user":
                msg_lower = msg["content"].lower()
                
                # Track product types mentioned
                product_type_map = {
                    "shirt": ["shirt", "shirts", "blouse", "top", "tee"],
                    "pants": ["pant", "pants", "jean", "jeans", "trouser", "trousers"],
                    "shoes": ["shoe", "shoes", "sneaker", "sneakers", "boot", "boots"]
                }
                
                for type_name, keywords in product_type_map.items():
                    if any(keyword in msg_lower for keyword in keywords):
                        context_info["last_product_type"] = type_name.rstrip('s')
                        break
                
                # Track searches
                if any(word in msg_lower for word in ["show", "find", "search", "looking"]):
                    context_info["previous_searches"].append(msg["content"])
        
        # Analyze current message for follow-up intent
        current_lower = current_message.lower()
        follow_up_phrases = [
            "show me more", "similar", "like these", "other options", 
            "different", "cheaper", "expensive", "better", "other colors"
        ]
        
        for phrase in follow_up_phrases:
            if phrase in current_lower:
                context_info["follow_up_intent"] = phrase
                break
        
        # Check for referential phrases
        referential_phrases = ["these", "those", "the last ones", "previous", "earlier"]
        context_info["has_reference"] = any(phrase in current_lower for phrase in referential_phrases)
        
        return context_info
    
    def _generate_contextual_greeting(self, message: str, context_info: Dict) -> str:
        """Generate appropriate greeting based on context"""
        if context_info["is_first_message"]:
            return "Hello! I'm your shopping assistant. "
        elif context_info["follow_up_intent"]:
            if context_info["follow_up_intent"] == "show me more":
                return "I'll find more options for you. "
            elif context_info["follow_up_intent"] == "similar":
                return "Looking for similar products... "
            elif context_info["follow_up_intent"] in ["cheaper", "expensive"]:
                return "Let me adjust the price range for you. "
            else:
                return "I understand you want different options. "
        elif context_info["has_reference"]:
            return "Based on our previous conversation, "
        else:
            return "Continuing our search, "


class ShoppingAgentFactory:
    """Factory for creating shopping agents with different configurations"""
    
    @staticmethod
    def create_agent(config: Dict[str, Any]) -> ShoppingAgent:
        """
        Create a shopping agent from configuration
        
        Args:
            config: Configuration dictionary with provider, model, and API keys
            
        Returns:
            Configured ShoppingAgent instance
        """
        model = config.get('llm_model', 'gemini-2.0-flash')
        
        # For Google ADK, we use Gemini models
        if 'openai' in config.get('llm_provider', '').lower():
            # Map OpenAI models to Gemini equivalents
            if 'gpt-4' in model.lower():
                model = 'gemini-1.5-pro'
            elif 'gpt-3.5' in model.lower():
                model = 'gemini-1.5-flash'
            else:
                model = 'gemini-2.0-flash'
        
        # Create agent with Google ADK
        agent = ShoppingAgent(
            model=model,
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 500)
        )
        
        return agent