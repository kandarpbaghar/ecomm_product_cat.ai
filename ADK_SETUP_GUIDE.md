# Google ADK Shopping Agent Setup Guide

## Overview
Your shopping agent is now ADK-compatible! This guide shows you how to run it with Google's Agent Development Kit interface.

## Prerequisites ✅
- [x] Google ADK installed
- [x] Shopping agent code migrated to ADK format
- [x] Configuration files created

## Quick Start

### 1. Set up API Keys

Edit the `.env.adk` file and add your API keys:

```bash
# Open the file
nano .env.adk

# Add your keys
GOOGLE_API_KEY=your-actual-google-api-key
OPENAI_API_KEY=your-actual-openai-api-key
```

**Get Google API Key:**
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key and paste it in `.env.adk`

### 2. Run the Agent

You have several options:

#### Option A: Using the setup script (Recommended)
```bash
python run_adk_agent.py
```
This will show you a menu with different interface options.

#### Option B: Direct ADK commands
```bash
# Web interface (opens in browser)
adk web --agent adk_shopping_agent:agent

# Terminal interface
adk run --agent adk_shopping_agent:agent

# API server
adk api_server --agent adk_shopping_agent:agent
```

#### Option C: Load environment and run
```bash
# Load environment variables
source .env.adk  # or: export $(cat .env.adk | xargs)

# Then run any ADK command
adk web --agent adk_shopping_agent:agent
```

## Features Available in ADK Interface

Your shopping agent now has these ADK-compatible tools:

1. **search_products**: Search for products by text description
2. **search_by_image**: Find similar products using image uploads
3. **filter_by_criteria**: Filter products by price, vendor, etc.
4. **get_product_info**: Get detailed product information
5. **find_similar_items**: Find alternatives to a product

## Example Conversations

Once running, you can interact with queries like:

- "Find me running shoes"
- "Show me products under $100"  
- "Find something like this [upload image]"
- "Tell me more about product 123"
- "Show me similar to product 456"

## Web Interface Features

The ADK web interface provides:

- 🌐 **Clean UI**: Modern web interface for chatting
- 📷 **Image Upload**: Drag and drop image search
- 📊 **Tool Visualization**: See which tools are being used
- 💾 **Session Management**: Conversation history
- 🔍 **Debug Mode**: View internal tool calls and responses

## Troubleshooting

### Missing API Key Error
```
❌ Missing required environment variables: GOOGLE_API_KEY
```
**Solution**: Add your Google API key to `.env.adk`

### Import Errors
```
ModuleNotFoundError: No module named 'shopping_agent'
```
**Solution**: Make sure you're running from the project root directory

### Weaviate Connection Issues
```
WEAVIATE] Failed to connect to http://localhost:8080
```
**Solution**: Make sure Weaviate is running:
```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/meta

# Or start your existing Flask app first (which starts Weaviate)
python ai_ecomm.py
```

### Database Issues
```
sqlite3.OperationalError: no such table
```
**Solution**: Make sure your database is set up. Run your existing Flask app once to initialize tables.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ADK Web UI    │────│  ADK Agent      │────│  Your Shopping  │
│                 │    │  (adk_shopping_ │    │  Agent Logic    │
│ - Chat Interface│    │   agent.py)     │    │                 │
│ - Image Upload  │    │                 │    │ - Weaviate      │
│ - Tool Viz      │    │ - Tool Wrappers │    │ - Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Files Created

- `adk_shopping_agent.py`: ADK-compatible agent wrapper
- `adk_config.yaml`: ADK configuration
- `.env.adk`: Environment variables
- `run_adk_agent.py`: Easy startup script
- `setup_adk.py`: Initial setup script

## Next Steps

1. **Test the Interface**: Try different types of queries
2. **Customize UI**: Modify `adk_config.yaml` for custom branding
3. **Add More Tools**: Extend `adk_shopping_agent.py` with additional capabilities
4. **Deploy**: Use ADK's deployment features for production

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all API keys are set correctly
3. Ensure Weaviate and your database are accessible
4. Check the ADK documentation: https://google.github.io/adk-docs/

---

🎉 **You're all set!** Your shopping agent now runs with Google's powerful ADK interface.