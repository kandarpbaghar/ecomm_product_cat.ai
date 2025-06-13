# AI-Powered Image Search Setup Guide

## Overview

This system now supports advanced image search capabilities using OpenAI's vision models and embeddings. Products can be searched using:

1. **Text queries** - Traditional keyword search
2. **Image uploads** - Find similar products by uploading an image
3. **Combined search** - Both text and image for precise results

## Setup Instructions

### 1. Configure OpenAI API Key

1. **Get an OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create an account and generate an API key
   - Copy the key (starts with `sk-`)

2. **Configure in the Application**:
   - Navigate to **Vector Configuration** page (`/vector_config`)
   - Enter your OpenAI API key in the "OpenAI API Key" field
   - Choose an image embedding model (default: `clip-vit-base-patch32`)
   - Save the configuration

3. **Alternative: Environment Variable**:
   ```bash
   export OPENAI_API_KEY="sk-your-api-key-here"
   ```

### 2. Index Products with Image Embeddings

#### Option A: Use the Web Interface
1. Go to **Vector Configuration** page
2. Click "Reindex All Products"
3. Wait for the process to complete (this may take time for large catalogs)

#### Option B: Use the Command Line Script
```bash
python reindex_with_images.py
```

This script will:
- Generate AI descriptions for all product images
- Create embeddings for image search
- Update the Weaviate index with the new data

### 3. How It Works

#### Image Processing Pipeline
1. **Image Download**: Product images are downloaded from URLs
2. **AI Description**: GPT-4V generates detailed descriptions of each image
3. **Embedding Generation**: Text embeddings are created from descriptions
4. **Indexing**: Both descriptions and embeddings are stored in Weaviate

#### Search Process
1. **Query Image Upload**: User uploads an image to search
2. **Description Generation**: GPT-4V describes the uploaded image
3. **Embedding Creation**: Text embedding is generated from the description
4. **Similarity Search**: Cosine similarity is calculated against all product embeddings
5. **Results Ranking**: Products are ranked by similarity score

## API Usage

### Text Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "text",
    "query": "blue shirt"
  }'
```

### Image Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "image",
    "image": "base64_encoded_image_data"
  }'
```

### Combined Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "text_image",
    "query": "summer",
    "image": "base64_encoded_image_data"
  }'
```

## Features

### AI-Generated Descriptions
- **Automatic**: Every product image gets an AI-generated description
- **Detailed**: Includes color, style, material, features, and overall appearance
- **Search-Optimized**: Descriptions are crafted for better search relevance

### Similarity Scoring
- **Cosine Similarity**: Mathematical similarity between image embeddings
- **Ranking**: Results sorted by relevance (highest similarity first)
- **Threshold**: Low-similarity results can be filtered out

### Fallback Handling
- **Graceful Degradation**: System works even without OpenAI configuration
- **Error Recovery**: Falls back to basic search if image processing fails
- **Status Logging**: Detailed logs for troubleshooting

## Configuration Options

### Image Embedding Models
- **clip-vit-base-patch32**: Default, good balance of speed and accuracy
- **openai-ada-002**: OpenAI's text embedding model (description-based)
- **openai-clip**: Direct image embeddings (when available)

### Performance Settings
- **Timeout**: API request timeout (default: 30 seconds)
- **Batch Size**: Number of products processed at once
- **Cache Duration**: How long to cache embeddings

## Troubleshooting

### Common Issues

1. **"OpenAI not configured"**
   - Verify API key is set correctly
   - Check API key has sufficient credits
   - Ensure API key has access to GPT-4V

2. **"Failed to generate image embedding"**
   - Check image URL accessibility
   - Verify image format is supported (JPEG, PNG)
   - Ensure image size is reasonable (<10MB)

3. **"No products indexed"**
   - Run the reindexing process
   - Check Weaviate connection status
   - Verify products have images

### Logs and Debugging
- Check console output for detailed processing logs
- Image download and processing status is logged
- Similarity scores are shown in search results

## Cost Considerations

### OpenAI API Usage
- **Image Description**: ~$0.01-0.02 per image (GPT-4V)
- **Text Embeddings**: ~$0.0001 per 1K tokens (embeddings)
- **Search Queries**: ~$0.01-0.02 per image search

### Optimization Tips
- **Batch Processing**: Index products during off-peak hours
- **Caching**: Embeddings are stored permanently to avoid re-processing
- **Model Selection**: Use appropriate models for your accuracy needs

## Security

- **API Key Protection**: Store keys securely, never commit to version control
- **Rate Limiting**: OpenAI has built-in rate limits
- **Data Privacy**: Images are processed by OpenAI's API (review their terms)

## Future Enhancements

Potential improvements:
- **Local Models**: Use local CLIP models to reduce API costs
- **Batch Processing**: Process multiple images in single API calls
- **Advanced Filters**: Combine embeddings with traditional filters
- **User Feedback**: Learn from user interactions to improve relevance