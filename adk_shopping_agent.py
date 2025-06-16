"""
ADK-compatible Shopping Agent
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools import tool
import base64

# Import your existing shopping agent components
from shopping_agent.agent import (
    search_products_by_text,
    search_products_by_image, 
    filter_products,
    get_product_details,
    get_similar_products
)


@tool
def search_products(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search for products using natural language query"""
    result = search_products_by_text(query, limit)
    return result


@tool  
def search_by_image(image_base64: str, limit: int = 10) -> Dict[str, Any]:
    """Search for similar products using an image"""
    result = search_products_by_image(image_base64, limit)
    return result


@tool
def filter_by_criteria(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    vendors: Optional[List[str]] = None,
    in_stock: bool = True,
    limit: int = 20
) -> Dict[str, Any]:
    """Filter products by various criteria like price, vendor, stock status"""
    result = filter_products(
        categories=None,
        vendors=vendors,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        limit=limit
    )
    return result


@tool
def get_product_info(product_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific product"""
    result = get_product_details(product_id)
    return result


@tool
def find_similar_items(product_id: int, limit: int = 5) -> Dict[str, Any]:
    """Find products similar to a given product"""
    result = get_similar_products(product_id, limit)
    return result


# Create the ADK agent
shopping_agent = Agent(
    name="shopping_assistant",
    model="gemini-2.0-flash-exp",
    description="AI Shopping Assistant for E-commerce Product Search",
    instruction="""You are an intelligent shopping assistant that helps users find products.

Your capabilities include:
1. **Product Search**: Search for products by text description
2. **Image Search**: Find similar products based on uploaded images  
3. **Price Filtering**: Filter products by price ranges
4. **Product Details**: Get detailed information about specific products
5. **Similar Products**: Find alternatives to a given product
6. **Vendor Filtering**: Search by specific brands or vendors

**Important Guidelines:**
- Always provide helpful, accurate product recommendations
- When users mention price constraints, use the filter_by_criteria tool
- For image-based queries, use the search_by_image tool
- Maintain context across the conversation
- If users ask for "similar" or "like this", ask for product ID or use image search
- Be conversational and friendly while being informative

**Example Interactions:**
- "Find me running shoes" → Use search_products
- "Show me pants under $100" → Use filter_by_criteria with max_price=100
- "Find something like this [image]" → Use search_by_image
- "Tell me more about product 123" → Use get_product_info
- "Show me similar to product 456" → Use find_similar_items

Always format product information clearly and suggest follow-up actions.""",
    tools=[
        search_products,
        search_by_image,
        filter_by_criteria,
        get_product_info,
        find_similar_items
    ]
)


# Export the agent for ADK discovery
agent = shopping_agent


if __name__ == "__main__":
    # For local testing
    print("Shopping Agent ADK Interface")
    print("Available tools:")
    for tool_func in shopping_agent.tools:
        print(f"- {tool_func.name}: {tool_func.description}")