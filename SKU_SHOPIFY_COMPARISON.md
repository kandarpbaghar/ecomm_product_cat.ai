# SKU Model vs Shopify Product Comparison

## Current SKU Model Fields

### ✅ **Fields We Have (Matching Shopify)**
| Field | SKU Model | Shopify Field | Status |
|-------|-----------|---------------|---------|
| `shopify_id` | ✅ | `id` | ✅ Mapped |
| `title` | ✅ | `title` | ✅ Mapped |
| `handle` | ✅ | `handle` | ✅ Mapped |
| `description` | ✅ | `body_html` | ✅ Mapped |
| `body_html` | ✅ | `body_html` | ✅ Mapped |
| `vendor` | ✅ | `vendor` | ✅ Mapped |
| `product_type` | ✅ | `product_type` | ✅ Mapped |
| `tags` | ✅ | `tags` | ✅ Mapped |
| `status` | ✅ | `status` | ✅ Mapped |
| `created_at` | ✅ | `created_at` | ✅ Mapped |
| `updated_at` | ✅ | `updated_at` | ✅ Mapped |
| `published_at` | ✅ | `published_at` | ✅ Mapped |

### ❌ **Missing Fields (Available in Shopify)**

#### **Product Level Fields**
| Shopify Field | Type | Description | Priority |
|---------------|------|-------------|----------|
| `template_suffix` | String | Custom template suffix | Medium |
| `published_scope` | String | Publication scope (web, global) | Medium |
| `admin_graphql_api_id` | String | GraphQL API ID | Low |

#### **Variant Level Fields (Missing)**
| Shopify Field | Type | Description | Priority |
|---------------|------|-------------|----------|
| `inventory_policy` | String | deny/continue when out of stock | High |
| `fulfillment_service` | String | manual/automatic fulfillment | High |
| `taxable` | Boolean | Whether item is taxable | High |
| `grams` | Integer | Weight in grams | Medium |
| `image_id` | String | Associated image ID | Medium |
| `inventory_item_id` | String | Inventory item ID | Medium |
| `old_inventory_quantity` | Integer | Previous inventory quantity | Low |
| `requires_shipping` | Boolean | Whether item requires shipping | High |
| `admin_graphql_api_id` | String | GraphQL API ID | Low |

#### **Image Level Fields (Missing)**
| Shopify Field | Type | Description | Priority |
|---------------|------|-------------|----------|
| `variant_ids` | Array | Associated variant IDs | Medium |
| `admin_graphql_api_id` | String | GraphQL API ID | Low |

#### **Product Options (New Structure Needed)**
| Shopify Field | Type | Description | Priority |
|---------------|------|-------------|----------|
| `options` | Array | Product options (Size, Color, etc.) | High |
| `options[].name` | String | Option name | High |
| `options[].position` | Integer | Option position | High |
| `options[].values` | Array | Option values | High |

## Priority Fields to Add

### **HIGH PRIORITY** (Business Critical)
1. **`inventory_policy`** - Controls what happens when out of stock
2. **`fulfillment_service`** - Controls order fulfillment
3. **`taxable`** - Tax calculation requirements
4. **`requires_shipping`** - Shipping calculation requirements
5. **Product Options** - Size, Color, etc. variants

### **MEDIUM PRIORITY** (Enhanced Functionality)
1. **`template_suffix`** - Custom product templates
2. **`published_scope`** - Publication control
3. **`grams`** - Weight in standard units
4. **`image_id`** - Better image association
5. **`variant_ids`** in images - Image-variant relationships

### **LOW PRIORITY** (API Completeness)
1. **`admin_graphql_api_id`** fields - GraphQL compatibility
2. **`old_inventory_quantity`** - Historical tracking

## Recommended Database Schema Updates

### 1. **Update SKU Model**
```sql
ALTER TABLE skus ADD COLUMN template_suffix VARCHAR(255);
ALTER TABLE skus ADD COLUMN published_scope VARCHAR(50) DEFAULT 'web';
ALTER TABLE skus ADD COLUMN admin_graphql_api_id VARCHAR(255);
```

### 2. **Update SKUVariant Model**
```sql
ALTER TABLE sku_variants ADD COLUMN inventory_policy VARCHAR(50) DEFAULT 'deny';
ALTER TABLE sku_variants ADD COLUMN fulfillment_service VARCHAR(50) DEFAULT 'manual';
ALTER TABLE sku_variants ADD COLUMN taxable BOOLEAN DEFAULT true;
ALTER TABLE sku_variants ADD COLUMN grams INTEGER;
ALTER TABLE sku_variants ADD COLUMN image_id VARCHAR(50);
ALTER TABLE sku_variants ADD COLUMN inventory_item_id VARCHAR(50);
ALTER TABLE sku_variants ADD COLUMN old_inventory_quantity INTEGER;
ALTER TABLE sku_variants ADD COLUMN requires_shipping BOOLEAN DEFAULT true;
ALTER TABLE sku_variants ADD COLUMN admin_graphql_api_id VARCHAR(255);
```

### 3. **Update SKUImage Model**
```sql
ALTER TABLE sku_images ADD COLUMN variant_ids TEXT; -- JSON array of variant IDs
ALTER TABLE sku_images ADD COLUMN admin_graphql_api_id VARCHAR(255);
```

### 4. **New ProductOption Model**
```sql
CREATE TABLE product_options (
    id INTEGER PRIMARY KEY,
    sku_id INTEGER REFERENCES skus(id),
    shopify_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    position INTEGER DEFAULT 0,
    values TEXT, -- JSON array of values
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Impact Analysis

### **Current Sync Process**
- ✅ **Working**: Basic product information sync
- ❌ **Missing**: Tax settings, fulfillment options, inventory policies
- ❌ **Missing**: Product options (sizes, colors, etc.)

### **E-commerce Functionality Impact**
1. **Tax Calculation**: Missing `taxable` field
2. **Shipping Calculation**: Missing `requires_shipping` field  
3. **Inventory Management**: Missing `inventory_policy` field
4. **Product Variants**: Missing proper options structure
5. **Order Fulfillment**: Missing `fulfillment_service` field

### **Search/Display Impact**
1. **Product Options**: Can't search by size, color, etc.
2. **Template Control**: Can't use custom product templates
3. **Image Variants**: Can't associate specific images with variants

## Recommendations

### **Phase 1: Critical Business Fields**
1. Add inventory policy, taxable, requires_shipping, fulfillment_service
2. Create product options table and relationships
3. Update sync process for these fields

### **Phase 2: Enhanced Features**
1. Add template suffix and published scope
2. Add image-variant relationships
3. Add grams and inventory item tracking

### **Phase 3: API Completeness**
1. Add all GraphQL API IDs
2. Add historical tracking fields
3. Implement full bidirectional sync