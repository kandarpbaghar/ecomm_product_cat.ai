"""
System prompts and conversation templates for the shopping agent
"""

SYSTEM_PROMPTS = {
    "shopping_assistant": """You are a helpful and knowledgeable shopping assistant for an e-commerce store. Your role is to help customers find the perfect products based on their needs and preferences.

Key behaviors:
1. Be friendly, professional, and conversational
2. Ask clarifying questions to better understand customer needs
3. Provide helpful product recommendations with clear explanations
4. Mention key product features, prices, and availability
5. Offer to show similar products or alternatives when appropriate
6. Help compare products when customers are deciding between options

When searching for products:
- Use natural language understanding to interpret what the customer wants
- Consider factors like price range, brand preferences, and specific features
- Show a reasonable number of results (typically 3-5) unless asked for more
- Explain why you're recommending specific products

When customers provide images:
- Acknowledge that you've received the image
- Describe what you see briefly
- Search for similar products and explain the similarities

Always maintain context throughout the conversation and remember previous preferences mentioned by the customer.""",

    "greeting": """Welcome! I'm your personal shopping assistant. I'm here to help you find exactly what you're looking for. 

You can:
- Describe what you're searching for in your own words
- Share an image of a product you like, and I'll find similar items
- Ask me to filter by price, brand, or other features
- Request comparisons between products

What can I help you find today?""",

    "clarification": """I'd be happy to help you find the perfect {product_type}. To give you the best recommendations, could you tell me a bit more about:

- Your preferred price range
- Any specific brands you like or want to avoid
- Key features that are important to you
- The intended use or occasion

This will help me narrow down the options to find exactly what you need.""",

    "no_results": """I couldn't find any products matching your exact criteria. This might be because:

1. The specific combination of features you're looking for isn't available
2. Products might be temporarily out of stock
3. I might need to adjust the search parameters

Would you like me to:
- Show you similar products with slightly different features?
- Broaden the search to include more options?
- Try searching for a different product category?""",

    "recommendation": """Based on what you're looking for, I found these great options:

{products}

Each of these products matches your criteria for {criteria}. Would you like me to:
- Show you more details about any of these products?
- Find similar alternatives?
- Help you compare specific products?""",

    "comparison": """Here's a comparison of the products you're interested in:

{comparison_table}

Key differences:
{key_differences}

Based on your preferences for {preferences}, I would recommend {recommendation} because {reason}.

Would you like more information about any of these products?""",

    "image_search": """I can see you've shared an image of {image_description}. Let me find similar products for you...

I found these items that match the style and features of what you showed me:

{products}

These products are similar in terms of {similarity_aspects}. Would you like to:
- See more options like these?
- Filter by specific features or price?
- Get more details about any of these products?""",

    "closing": """It was my pleasure helping you today! Here's a summary of what we discussed:

{summary}

Before you go:
- Is there anything else you'd like to know about these products?
- Would you like me to find any other items?
- Do you need help with sizing, shipping, or other information?

Feel free to come back anytime you need shopping assistance!"""
}

# Response templates for common scenarios
RESPONSE_TEMPLATES = {
    "price_filter": "I'll show you products within your budget of {price_range}.",
    
    "brand_preference": "I'll focus on {brands} products as you requested.",
    
    "feature_request": "I'll look for products with {features}.",
    
    "out_of_stock": "Unfortunately, this item is currently out of stock. Would you like me to show you similar alternatives?",
    
    "single_product": "Here's detailed information about the product you asked about:\n\n{product_details}",
    
    "multiple_products": "I found {count} products that match what you're looking for. Here are the top options:",
    
    "follow_up_suggestions": [
        "Would you like to see more options?",
        "Should I filter these by a specific feature?",
        "Do you want to compare any of these products?",
        "Would you like more details about any item?",
        "Should I search for something else?"
    ]
}

# Error messages
ERROR_MESSAGES = {
    "general_error": "I apologize, but I encountered an issue while searching. Please try again or rephrase your request.",
    
    "connection_error": "I'm having trouble connecting to the product database. Please try again in a moment.",
    
    "invalid_image": "I couldn't process the image you shared. Please make sure it's a valid image file (JPG, PNG, etc.).",
    
    "rate_limit": "I'm receiving too many requests right now. Please wait a moment before trying again."
}

def format_product_display(product: dict) -> str:
    """Format a single product for display in chat"""
    return f"""**{product.get('title', 'Untitled Product')}**
Price: ${product.get('price', 'N/A')}
{product.get('description', 'No description available')[:100]}...
Stock: {'In Stock' if product.get('quantity', 0) > 0 else 'Out of Stock'}
"""

def format_product_comparison(products: list) -> str:
    """Format multiple products for comparison"""
    comparison = "| Feature | "
    comparison += " | ".join([f"Product {i+1}" for i in range(len(products))]) + " |\n"
    comparison += "|---------|" + "---------|" * len(products) + "\n"
    
    # Add comparison rows
    features = ['title', 'price', 'vendor', 'stock']
    for feature in features:
        comparison += f"| {feature.title()} | "
        for product in products:
            if feature == 'stock':
                value = 'In Stock' if product.get('quantity', 0) > 0 else 'Out of Stock'
            elif feature == 'price':
                value = f"${product.get(feature, 'N/A')}"
            else:
                value = product.get(feature, 'N/A')
            comparison += f"{value} | "
        comparison += "\n"
    
    return comparison