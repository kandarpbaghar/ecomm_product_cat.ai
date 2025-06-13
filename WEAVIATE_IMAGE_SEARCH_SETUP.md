# Weaviate Image Search Setup

## Current Status
The current Weaviate setup uses `text2vec-transformers` which only supports text vectorization. Image search is currently implemented as a fallback that returns all products.

## To Enable True Image Search

### Option 1: Use multi2vec-clip (Recommended)

1. Update the vectorizer in your Weaviate configuration:
   ```python
   # In weaviate_service.py, line 17
   self.vectorizer = 'multi2vec-clip'
   ```

2. Make sure your Weaviate instance supports CLIP:
   - If using Docker: Use `semitechnologies/weaviate:latest` with the `multi2vec-clip` module
   - Update your docker-compose.yml to include:
   ```yaml
   weaviate:
     image: semitechnologies/weaviate:latest
     environment:
       ENABLE_MODULES: 'multi2vec-clip'
       CLIP_INFERENCE_API: 'http://multi2vec-clip:8080'
   ```

3. Restart your Weaviate instance and re-index your products:
   ```bash
   python reindex_weaviate.py
   ```

### Option 2: Use OpenAI embeddings

1. Set up OpenAI API key and update vectorizer:
   ```python
   self.vectorizer = 'multi2vec-openai'
   ```

2. Configure your Weaviate with OpenAI module enabled

### Current Fallback Behavior

When image search is used with the current setup:
- Returns all products (up to the limit)
- Logs that image search is not supported
- For combined text+image search, prioritizes text search if query is provided

### Testing

Test image search functionality:
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"search_type": "image", "image": "base64_image_data"}'
```

The system will gracefully fall back to returning available products when true image vectorization is not available.