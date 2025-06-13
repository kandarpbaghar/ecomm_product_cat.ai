#!/usr/bin/env python3
"""
Script to re-index all products in Weaviate with image embeddings
"""
from ai_ecomm import create_app
from database import db
from models.sku import SKU
from services.weaviate_service import WeaviateService

def reindex_all_products_with_images():
    """Re-index all products in the database to Weaviate with image embeddings"""
    app = create_app()
    
    with app.app_context():
        # Initialize Weaviate service
        print("Initializing Weaviate service...")
        weaviate_service = WeaviateService()
        
        # Check if OpenAI is configured
        if not weaviate_service.openai_service or not weaviate_service.openai_service.is_configured():
            print("WARNING: OpenAI is not configured. Image embeddings will not be generated.")
            print("Please configure OpenAI API key in the vector configuration page.")
            return
        
        # Get all SKUs
        skus = SKU.query.all()
        print(f"Found {len(skus)} products to index")
        
        if not skus:
            print("No products found in database")
            return
        
        # Clear existing Weaviate data first
        try:
            print("Clearing existing Weaviate data...")
            weaviate_service.client.schema.delete_class("Product")
            weaviate_service.setup_schema()
            print("Weaviate schema recreated with image embedding support")
        except Exception as e:
            print(f"Error clearing Weaviate: {e}")
        
        # Index each product
        successful = 0
        failed = 0
        
        for i, sku in enumerate(skus, 1):
            try:
                print(f"[{i}/{len(skus)}] Indexing product: {sku.title}")
                
                # Convert SKU to dict for Weaviate
                product_data = sku.to_dict()
                
                # Add to Weaviate (this will generate image embeddings)
                weaviate_id = weaviate_service.add_product(product_data)
                
                if weaviate_id:
                    # Update the SKU with the new weaviate_id
                    sku.weaviate_id = weaviate_id
                    db.session.commit()
                    successful += 1
                    print(f"  ✓ Successfully indexed with ID: {weaviate_id}")
                else:
                    failed += 1
                    print(f"  ✗ Failed to index")
                    
            except Exception as e:
                failed += 1
                print(f"  ✗ Error indexing product {sku.id}: {e}")
                db.session.rollback()
        
        print(f"\nIndexing complete:")
        print(f"  Successfully indexed: {successful}")
        print(f"  Failed: {failed}")
        
        # Verify the indexing worked
        try:
            count_result = (
                weaviate_service.client.query
                .aggregate("Product")
                .with_meta_count()
                .do()
            )
            
            total_in_weaviate = count_result.get('data', {}).get('Aggregate', {}).get('Product', [{}])[0].get('meta', {}).get('count', 0)
            print(f"  Total products now in Weaviate: {total_in_weaviate}")
            
            # Check how many have image embeddings
            result = (
                weaviate_service.client.query
                .get("Product", ["product_id", "image_embedding", "image_description"])
                .with_limit(100)
                .do()
            )
            
            products = result.get('data', {}).get('Get', {}).get('Product', [])
            with_embeddings = sum(1 for p in products if p.get('image_embedding'))
            with_descriptions = sum(1 for p in products if p.get('image_description'))
            
            print(f"  Products with image embeddings: {with_embeddings}")
            print(f"  Products with image descriptions: {with_descriptions}")
            
        except Exception as e:
            print(f"Error verifying indexing: {e}")

if __name__ == "__main__":
    print("Starting product indexing with image embeddings...")
    print("This will generate AI descriptions and embeddings for all product images.")
    print("Make sure you have configured your OpenAI API key in the vector configuration.")
    print()
    
    # Ask for confirmation
    response = input("Continue? (y/N): ")
    if response.lower() == 'y':
        reindex_all_products_with_images()
    else:
        print("Cancelled.")