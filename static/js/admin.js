// Admin functionality
$(document).ready(function() {
    // Don't auto-load categories anymore since they're in a dedicated page
});

// Load categories management page
function loadCategories() {
    document.getElementById('contentFrame').src = '/admin/categories';
}

// Load product catalog page
function loadCatalog() {
    document.getElementById('contentFrame').src = '/catalog';
}

// Load categories for dropdowns (used by modals)
async function loadCategoriesForDropdowns() {
    try {
        const data = await apiCall('/categories');
        const categorySelect = $('#categoryParent, #skuCategories');
        
        categorySelect.empty().append('<option value="">None</option>');
        
        data.categories.forEach(category => {
            categorySelect.append(`<option value="${category.id}">${category.name}</option>`);
        });
    } catch (error) {
        showToast('Failed to load categories', 'error');
    }
}

// Category CRUD
function showAddCategoryModal() {
    $('#categoryModalTitle').text('Add Category');
    $('#categoryForm')[0].reset();
    $('#categoryId').val('');
    loadCategoriesForDropdowns(); // Load categories for parent dropdown
    $('#categoryModal').modal('show');
}

async function editCategory(id) {
    // Find the edit button and show loading state
    const $editBtn = $(`button[onclick="editCategory(${id})"]`);
    const originalBtnHtml = $editBtn.html();
    $editBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');
    
    try {
        const category = await apiCall(`/categories/${id}`);
        await loadCategoriesForDropdowns(); // Load categories for parent dropdown
        $('#categoryModalTitle').text('Edit Category');
        $('#categoryId').val(category.id);
        $('#categoryName').val(category.name);
        $('#categoryHandle').val(category.handle);
        $('#categoryDescription').val(category.description);
        $('#categoryParent').val(category.parent_id);
        $('#categoryModal').modal('show');
    } catch (error) {
        showToast('Failed to load category', 'error');
    } finally {
        // Restore button state
        $editBtn.prop('disabled', false).html(originalBtnHtml);
    }
}

async function saveCategory() {
    const id = $('#categoryId').val();
    const data = {
        name: $('#categoryName').val(),
        handle: $('#categoryHandle').val() || $('#categoryName').val().toLowerCase().replace(/\s+/g, '-'),
        description: $('#categoryDescription').val(),
        parent_id: $('#categoryParent').val() || null
    };
    
    // Show loading state
    const $saveBtn = $('#categoryModal .modal-footer button[onclick="saveCategory()"]');
    const originalBtnText = $saveBtn.html();
    $saveBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Saving...');
    
    try {
        if (id) {
            await apiCall(`/categories/${id}`, 'PUT', data);
            showToast('Category updated successfully');
        } else {
            await apiCall('/categories', 'POST', data);
            showToast('Category created successfully');
        }
        
        $('#categoryModal').modal('hide');
        // Refresh the categories page if it's currently displayed
        const contentFrame = document.getElementById('contentFrame');
        if (contentFrame.src.includes('/admin/categories')) {
            contentFrame.contentWindow.loadCategories();
        }
    } catch (error) {
        showToast('Failed to save category', 'error');
    } finally {
        // Restore button state
        $saveBtn.prop('disabled', false).html(originalBtnText);
    }
}

async function deleteCategory(id) {
    if (!confirm('Are you sure you want to delete this category?')) return;
    
    // Find the delete button and show loading state
    const $deleteBtn = $(`button[onclick="deleteCategory(${id})"]`);
    const originalBtnHtml = $deleteBtn.html();
    $deleteBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');
    
    try {
        await apiCall(`/categories/${id}`, 'DELETE');
        showToast('Category deleted successfully');
        // Refresh the categories page if it's currently displayed
        const contentFrame = document.getElementById('contentFrame');
        if (contentFrame.src.includes('/admin/categories')) {
            contentFrame.contentWindow.loadCategories();
        }
    } catch (error) {
        showToast('Failed to delete category', 'error');
        // Restore button state on error
        $deleteBtn.prop('disabled', false).html(originalBtnHtml);
    }
}

// SKU Management
async function loadSKUs() {
    document.getElementById('contentFrame').src = '/admin/skus';
}

// Load search page
function loadSearchPage() {
    document.getElementById('contentFrame').src = '/search';
}

// Load Shopify management page
function loadShopifyManagement() {
    document.getElementById('contentFrame').src = '/admin/shopify';
}

// Load Vector configuration page
function loadVectorConfig() {
    document.getElementById('contentFrame').src = '/admin/vector';
}

// Load Settings page
function loadSettings() {
    document.getElementById('contentFrame').src = '/admin/settings';
}

async function loadSKUsByCategory(categoryId) {
    document.getElementById('contentFrame').src = `/admin/skus?category_id=${categoryId}`;
}

function showAddSKUModal() {
    $('#skuModalTitle').text('Add Product');
    $('#skuForm')[0].reset();
    $('#skuId').val('');
    clearSKUImage();
    clearVariants();
    resetTabs();
    
    // Set defaults
    $('#skuStatus').val('active');
    $('#skuPublishedScope').val('web');
    $('#skuTrackQuantity').prop('checked', true);
    $('#skuTaxable').prop('checked', true);
    $('#skuRequiresShipping').prop('checked', true);
    $('#skuInventoryPolicy').val('deny');
    $('#skuWeightUnit').val('kg');
    $('#skuFulfillmentService').val('manual');
    
    loadCategoriesForDropdowns();
    loadVendorsAndTypes();
    $('#lastSaved').text('');
    $('#skuModal').modal('show');
}

// SKU Image handling functions
let selectedSKUImage = null;
let selectedSKUImageUrl = null;

function handleSKUImageSelect(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.type.startsWith('image/')) {
            if (file.size > 16 * 1024 * 1024) {
                showToast('Image file is too large. Please select an image under 16MB.', 'error');
                return;
            }
            selectedSKUImage = file;
            selectedSKUImageUrl = null;
            displaySKUImagePreview(file);
            $('#skuImageUrl').val(''); // Clear URL field
        } else {
            showToast('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
        }
    }
}

function handleSKUImageUrl() {
    const url = $('#skuImageUrl').val();
    if (url) {
        selectedSKUImageUrl = url;
        selectedSKUImage = null;
        displaySKUImagePreviewFromUrl(url);
        $('#skuImageFile').val(''); // Clear file input
    } else {
        selectedSKUImageUrl = null;
    }
}

function displaySKUImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        $('#skuPreviewImg').attr('src', e.target.result);
        $('#skuImagePreview').removeClass('d-none');
    };
    reader.readAsDataURL(file);
}

function displaySKUImagePreviewFromUrl(url) {
    $('#skuPreviewImg').attr('src', url);
    $('#skuImagePreview').removeClass('d-none');
}

function clearSKUImage() {
    selectedSKUImage = null;
    selectedSKUImageUrl = null;
    $('#skuImageFile').val('');
    $('#skuImageUrl').val('');
    $('#skuImagePreview').addClass('d-none');
}

async function editSKU(id) {
    // Find the edit button and show loading state
    const $editBtn = $(`button[onclick="editSKU(${id})"]`);
    const originalBtnHtml = $editBtn.html();
    $editBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');
    
    try {
        console.log('Loading SKU:', id);
        const sku = await apiCall(`/skus/${id}`);
        console.log('SKU loaded:', sku);
        
        await loadCategoriesForDropdowns();
        await loadVendorsAndTypes();
        
        $('#skuModalTitle').text('Edit Product');
        $('#skuId').val(sku.id);
        
        // Basic Info
        $('#skuTitle').val(sku.title || '');
        $('#skuHandle').val(sku.handle || '');
        // Strip HTML tags from description for display in textarea
        const plainDescription = $('<div>').html(sku.description || '').text();
        $('#skuDescription').val(plainDescription);
        $('#skuBodyHtml').val(sku.body_html || '');
        
        // Pricing
        $('#skuPrice').val(sku.price || 0);
        $('#skuComparePrice').val(sku.compare_at_price || '');
        $('#skuTaxable').prop('checked', sku.taxable !== false);
        
        // Inventory
        $('#skuCode').val(sku.sku_code || '');
        $('#skuBarcode').val(sku.barcode || '');
        $('#skuTrackQuantity').prop('checked', sku.track_quantity !== false);
        $('#skuQuantity').val(sku.quantity || 0);
        $('#skuInventoryPolicy').val(sku.inventory_policy || 'deny');
        
        // Shipping
        $('#skuRequiresShipping').prop('checked', sku.requires_shipping !== false);
        $('#skuWeight').val(sku.weight || 0);
        $('#skuWeightUnit').val(sku.weight_unit || 'kg');
        $('#skuFulfillmentService').val(sku.fulfillment_service || 'manual');
        
        // SEO
        $('#skuMetaTitle').val(sku.meta_title || '');
        $('#skuMetaDescription').val(sku.meta_description || '');
        updateSEOPreview();
        
        // Organization
        $('#skuVendor').val(sku.vendor || '');
        $('#skuProductType').val(sku.product_type || '');
        // Handle tags - convert array back to comma-separated string
        const tagsValue = Array.isArray(sku.tags) ? sku.tags.join(', ') : (sku.tags || '');
        $('#skuTags').val(tagsValue);
        $('#skuStatus').val(sku.status || 'active');
        $('#skuPublishedScope').val(sku.published_scope || 'web');
        $('#skuTemplateSuffix').val(sku.template_suffix || '');
        
        // Set selected categories
        if (sku.categories && Array.isArray(sku.categories)) {
            const categoryIds = sku.categories.map(cat => cat.id);
            $('#skuCategories').val(categoryIds);
        }
        
        // Load existing images
        clearSKUImage();
        if (sku.images && sku.images.length > 0) {
            loadExistingImages(sku.images);
        }
        
        // Load variants and options
        if (sku.options && sku.options.length > 0) {
            $('#hasVariants').prop('checked', true);
            toggleVariants();
            loadExistingOptions(sku.options);
            if (sku.variants && sku.variants.length > 0) {
                loadExistingVariants(sku.variants);
            }
        }
        
        // Update last saved
        if (sku.updated_at) {
            $('#lastSaved').text(`Last saved: ${new Date(sku.updated_at).toLocaleString()}`);
        }
        
        resetTabs();
        $('#skuModal').modal('show');
    } catch (error) {
        console.error('Error loading product:', error);
        showToast('Failed to load product: ' + (error.message || 'Unknown error'), 'error');
    } finally {
        // Restore button state
        $editBtn.prop('disabled', false).html(originalBtnHtml);
    }
}

async function saveSKU(isDraft = false) {
    const id = $('#skuId').val();
    
    // Show loading state on all save buttons
    const $saveBtns = $('#skuModal .modal-footer button[onclick*="saveSKU"]');
    const originalBtnTexts = $saveBtns.map(function() { return $(this).html(); }).get();
    $saveBtns.prop('disabled', true);
    
    // Update the clicked button specifically
    $saveBtns.each(function() {
        const $btn = $(this);
        if ($btn.attr('onclick').includes('true') && isDraft) {
            $btn.html('<span class="spinner-border spinner-border-sm me-2"></span>Saving as Draft...');
        } else if ($btn.attr('onclick').includes('false') || !$btn.attr('onclick').includes('true')) {
            if (!isDraft) {
                $btn.html('<span class="spinner-border spinner-border-sm me-2"></span>Saving...');
            }
        }
    });
    
    // Prepare comprehensive data object
    const data = {
        // Basic Info
        title: $('#skuTitle').val(),
        handle: $('#skuHandle').val() || $('#skuTitle').val().toLowerCase().replace(/\s+/g, '-'),
        description: $('#skuDescription').val(),
        body_html: $('#skuBodyHtml').val(),
        
        // Pricing
        price: parseFloat($('#skuPrice').val()) || 0,
        compare_at_price: parseFloat($('#skuComparePrice').val()) || null,
        taxable: $('#skuTaxable').is(':checked'),
        
        // Inventory
        sku_code: $('#skuCode').val(),
        barcode: $('#skuBarcode').val(),
        track_quantity: $('#skuTrackQuantity').is(':checked'),
        quantity: parseInt($('#skuQuantity').val()) || 0,
        inventory_policy: $('#skuInventoryPolicy').val(),
        
        // Shipping
        requires_shipping: $('#skuRequiresShipping').is(':checked'),
        weight: parseFloat($('#skuWeight').val()) || 0,
        weight_unit: $('#skuWeightUnit').val(),
        fulfillment_service: $('#skuFulfillmentService').val(),
        
        // SEO
        meta_title: $('#skuMetaTitle').val(),
        meta_description: $('#skuMetaDescription').val(),
        
        // Organization
        vendor: $('#skuVendor').val(),
        product_type: $('#skuProductType').val(),
        tags: $('#skuTags').val(),
        status: isDraft ? 'draft' : $('#skuStatus').val(),
        published_scope: $('#skuPublishedScope').val(),
        template_suffix: $('#skuTemplateSuffix').val(),
        
        // Categories
        category_ids: $('#skuCategories').val() ? $('#skuCategories').val().map(id => parseInt(id)) : []
    };
    
    // Handle variants if enabled
    if ($('#hasVariants').is(':checked')) {
        data.options = collectProductOptions();
        data.variants = collectVariantData();
    }
    
    try {
        let response;
        
        // Check if we need to use FormData (for image uploads)
        if (selectedSKUImage || (selectedSKUImages && selectedSKUImages.length > 0)) {
            const formData = new FormData();
            
            // Add all data fields
            Object.keys(data).forEach(key => {
                if (Array.isArray(data[key])) {
                    if (key === 'category_ids') {
                        data[key].forEach(val => formData.append('category_ids', val));
                    } else {
                        formData.append(key, JSON.stringify(data[key]));
                    }
                } else if (data[key] !== null && data[key] !== undefined) {
                    formData.append(key, data[key]);
                }
            });
            
            // Add images
            if (selectedSKUImage) {
                formData.append('image', selectedSKUImage);
            }
            if (selectedSKUImages && selectedSKUImages.length > 0) {
                selectedSKUImages.forEach((img, index) => {
                    formData.append(`images`, img.file);
                });
            }
            
            const url = id ? `/api/skus/${id}` : '/api/skus';
            const method = id ? 'PUT' : 'POST';
            
            response = await fetch(url, {
                method: method,
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save product');
            }
            response = await response.json();
        } else {
            // Use regular JSON API
            if (id) {
                response = await apiCall(`/skus/${id}`, 'PUT', data);
            } else {
                response = await apiCall('/skus', 'POST', data);
            }
        }
        
        showToast(`Product ${id ? 'updated' : 'created'} successfully`);
        $('#skuModal').modal('hide');
        clearSKUImage();
        clearVariants();
        
        // Refresh the SKU list if it's currently displayed
        const contentFrame = document.getElementById('contentFrame');
        if (contentFrame.src.includes('/admin/skus')) {
            contentFrame.contentWindow.loadSKUs();
        }
    } catch (error) {
        console.error('Error saving product:', error);
        showToast(error.message || 'Failed to save product', 'error');
    } finally {
        // Restore button states
        $saveBtns.each(function(index) {
            $(this).prop('disabled', false).html(originalBtnTexts[index]);
        });
    }
}

async function deleteSKU(id) {
    if (!confirm('Are you sure you want to delete this SKU?')) return;
    
    // Find the delete button and show loading state
    const $deleteBtn = $(`button[onclick="deleteSKU(${id})"]`);
    const originalBtnHtml = $deleteBtn.html();
    $deleteBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');
    
    try {
        await apiCall(`/skus/${id}`, 'DELETE');
        showToast('SKU deleted successfully');
        // Refresh the SKU list if it's currently displayed
        const contentFrame = document.getElementById('contentFrame');
        if (contentFrame.src.includes('/admin/skus')) {
            contentFrame.contentWindow.loadSKUs();
        }
    } catch (error) {
        showToast('Failed to delete SKU', 'error');
        // Restore button state on error
        $deleteBtn.prop('disabled', false).html(originalBtnHtml);
    }
}


// API Documentation
function showAPIDoc(endpoint, methods) {
    $('#apiModalTitle').text(`API Documentation: ${endpoint}`);
    // Remove /api prefix if it exists since API_BASE already includes it
    const cleanPath = endpoint.startsWith('/api/') ? endpoint.substring(4) : endpoint;
    $('#apiPath').val(cleanPath);
    $('#apiMethod').val(methods[0]);
    
    // Show/hide image section for search endpoint
    if (endpoint === '/api/search') {
        $('#apiImageSection').show();
        // Listen for changes in the apiBody to detect search type
        $('#apiBody').off('input').on('input', function() {
            const body = $(this).val();
            if (body.includes('search_type: image') || body.includes('search_type: text_image')) {
                $('#apiImageSection').show();
            }
        });
    } else {
        $('#apiImageSection').hide();
    }
    
    const docContent = $('#apiDocContent');
    docContent.html(`
        <h5>Endpoint: ${endpoint}</h5>
        <p>Supported Methods: ${methods.map(m => `<span class="api-method ${m.toLowerCase()}">${m}</span>`).join(' ')}</p>
        
        ${generateAPIDocumentation(endpoint, methods)}
    `);
    
    $('#apiModal').modal('show');
}

function generateAPIDocumentation(endpoint, methods) {
    const docs = {
        '/api/categories': {
            GET: {
                description: 'Get all categories',
                parameters: 'page (int), per_page (int)',
                response: '{ categories: [...], total: int, page: int, pages: int }'
            },
            POST: {
                description: 'Create a new category',
                body: '{ name: string, handle: string, description: string, parent_id: int }',
                response: '{ id: int, name: string, ... }'
            }
        },
        '/api/categories/{id}': {
            GET: {
                description: 'Get a specific category',
                response: '{ id: int, name: string, ... }'
            },
            PUT: {
                description: 'Update a category',
                body: '{ name: string, handle: string, description: string, parent_id: int }',
                response: '{ id: int, name: string, ... }'
            },
            DELETE: {
                description: 'Delete a category',
                response: '{ message: string }'
            }
        },
        '/api/skus': {
            GET: {
                description: 'Get all SKUs',
                parameters: 'page (int), per_page (int), category_id (int)',
                response: '{ skus: [...], total: int, page: int, pages: int }'
            },
            POST: {
                description: 'Create a new SKU',
                body: '{ title: string, sku_code: string, price: float, ... }',
                response: '{ id: int, title: string, ... }'
            }
        },
        '/api/search': {
            POST: {
                description: 'Search products by text or image with optional catalog filters',
                body: 'FormData: search_type=text|image|text_image, query=string (for text), image=file (for image), filters=JSON (optional)',
                parameters: {
                    search_type: 'text, image, or text_image (combined search)',
                    query: 'Search query text (required for text search)',
                    image: 'Image file (required for image search)',
                    filters: 'JSON object with catalog filters (optional)'
                },
                sampleData: {
                    text: {
                        search_type: 'text',
                        query: 'blue shirt',
                        filters: JSON.stringify({
                            categories: ['1', '2'],
                            vendors: ['Nike', 'Adidas'],
                            productTypes: ['Clothing'],
                            minPrice: 10,
                            maxPrice: 100,
                            inStock: true,
                            outOfStock: false
                        }, null, 2)
                    },
                    image: {
                        search_type: 'image',
                        filters: JSON.stringify({
                            categories: ['3'],
                            minPrice: 50
                        }, null, 2)
                    },
                    combined: {
                        search_type: 'text_image',
                        query: 'running shoes',
                        filters: JSON.stringify({
                            vendors: ['Nike'],
                            minPrice: 80,
                            maxPrice: 200
                        }, null, 2)
                    }
                },
                response: '{ results: [{ product_id, title, description, price, image_url, vendor, product_type, _additional: { distance }, _source }] }'
            }
        },
        '/api/sync/shopify': {
            POST: {
                description: 'Start Shopify sync',
                body: '{ sync_type: "full"|"incremental" }',
                response: '{ message: string, sync_id: int }'
            }
        }
    };
    
    let html = '<div class="mt-3">';
    
    methods.forEach(method => {
        const docInfo = docs[endpoint]?.[method] || {};
        html += `
            <div class="api-endpoint">
                <h6>${method}</h6>
                ${docInfo.description ? `<p>${docInfo.description}</p>` : ''}
                ${docInfo.parameters ? (
                    typeof docInfo.parameters === 'object' ? 
                    `<p><strong>Parameters:</strong></p><ul>${Object.entries(docInfo.parameters).map(([key, value]) => 
                        `<li><strong>${key}:</strong> ${value}</li>`
                    ).join('')}</ul>` :
                    `<p><strong>Parameters:</strong> ${docInfo.parameters}</p>`
                ) : ''}
                ${docInfo.body ? `<p><strong>Request Body:</strong> <code>${docInfo.body}</code></p>` : ''}
                ${docInfo.response ? `<p><strong>Response:</strong> <code>${docInfo.response}</code></p>` : ''}
                ${docInfo.sampleData ? generateSampleDataSection(endpoint, method, docInfo.sampleData) : ''}
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function generateSampleDataSection(endpoint, method, sampleData) {
    let html = '<div class="mt-3"><p><strong>Sample Data:</strong></p>';
    
    Object.entries(sampleData).forEach(([key, sample]) => {
        html += `
            <div class="mb-2">
                <button class="btn btn-sm btn-outline-primary" onclick="fillSampleData('${endpoint}', '${method}', '${key}')">
                    Use ${key} example
                </button>
                ${key === 'image' ? '<small class="ms-2">(You\'ll need to select an image file)</small>' : ''}
                ${key === 'combined' ? '<small class="ms-2">(Select both text and image)</small>' : ''}
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function fillSampleData(endpoint, method, sampleKey) {
    const docs = {
        '/api/search': {
            POST: {
                sampleData: {
                    text: {
                        search_type: 'text',
                        query: 'blue shirt',
                        filters: JSON.stringify({
                            categories: ['1', '2'],
                            vendors: ['Nike', 'Adidas'],
                            productTypes: ['Clothing'],
                            minPrice: 10,
                            maxPrice: 100,
                            inStock: true,
                            outOfStock: false
                        }, null, 2)
                    },
                    image: {
                        search_type: 'image',
                        filters: JSON.stringify({
                            categories: ['3'],
                            minPrice: 50
                        }, null, 2)
                    },
                    combined: {
                        search_type: 'text_image',
                        query: 'running shoes',
                        filters: JSON.stringify({
                            vendors: ['Nike'],
                            minPrice: 80,
                            maxPrice: 200
                        }, null, 2)
                    }
                }
            }
        }
    };
    
    const sample = docs[endpoint]?.[method]?.sampleData?.[sampleKey];
    if (sample && endpoint === '/api/search') {
        // For search endpoint, we need to show FormData format
        let formDataStr = 'FormData:\n';
        Object.entries(sample).forEach(([key, value]) => {
            if (key === 'filters') {
                // For filters, show as compact JSON on single line
                const filterObj = JSON.parse(value);
                formDataStr += `${key}: ${JSON.stringify(filterObj)}\n`;
            } else {
                formDataStr += `${key}: ${value}\n`;
            }
        });
        $('#apiBody').val(formDataStr.trim());
    }
}

async function testAPI() {
    const method = $('#apiMethod').val();
    const path = $('#apiPath').val();
    const body = $('#apiBody').val();
    
    try {
        // Special handling for search endpoint
        if (path === '/search' && method === 'POST') {
            const formData = new FormData();
            
            // Parse FormData format
            const lines = body.split('\n').filter(line => line.trim());
            lines.forEach(line => {
                if (line.startsWith('FormData:')) return;
                
                const colonIndex = line.indexOf(':');
                if (colonIndex > -1) {
                    const key = line.substring(0, colonIndex).trim();
                    let value = line.substring(colonIndex + 1).trim();
                    
                    // Special handling for filters - ensure it's properly formatted JSON
                    if (key === 'filters' && value.startsWith('{')) {
                        try {
                            // Parse and re-stringify to ensure valid JSON
                            const parsed = JSON.parse(value);
                            value = JSON.stringify(parsed);
                        } catch (e) {
                            console.error('Invalid JSON in filters:', e);
                        }
                    }
                    
                    formData.append(key, value);
                    console.log(`FormData: ${key} = ${value}`); // Debug log
                }
            });
            
            // Add image if selected
            const imageInput = document.getElementById('apiImage');
            if (imageInput && imageInput.files.length > 0) {
                formData.append('image', imageInput.files[0]);
            }
            
            // Make the request
            const url = `${API_BASE}${path}`;
            console.log(`Making request to: ${url}`); // Debug log
            const response = await fetch(url, {
                method: method,
                body: formData
            });
            
            // Check content type
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Expected JSON response but got ${contentType}. Response: ${text.substring(0, 200)}...`);
            }
            
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'API request failed');
            }
            
            $('#apiResponse').text(JSON.stringify(result, null, 2));
        } else {
            // Regular JSON API call
            let data = null;
            if (body && (method === 'POST' || method === 'PUT')) {
                data = JSON.parse(body);
            }
            
            const result = await apiCall(path, method, data);
            $('#apiResponse').text(JSON.stringify(result, null, 2));
        }
    } catch (error) {
        $('#apiResponse').text(`Error: ${error.message}`);
    }
}

// New helper functions for enhanced SKU modal

// Tab management
function resetTabs() {
    $('#skuTabs .nav-link').removeClass('active');
    $('#skuTabs .nav-link:first').addClass('active');
    $('#skuTabContent .tab-pane').removeClass('show active');
    $('#skuTabContent .tab-pane:first').addClass('show active');
}

// Load vendors and product types for datalists
async function loadVendorsAndTypes() {
    try {
        const response = await fetch('/api/catalog/filters');
        const data = await response.json();
        
        // Populate vendors datalist
        const vendorsList = $('#vendorsList');
        vendorsList.empty();
        if (data.vendors) {
            data.vendors.forEach(vendor => {
                vendorsList.append(`<option value="${vendor.name}">`);
            });
        }
        
        // Populate product types datalist
        const typesList = $('#productTypesList');
        typesList.empty();
        if (data.productTypes) {
            data.productTypes.forEach(type => {
                typesList.append(`<option value="${type.name}">`);
            });
        }
    } catch (error) {
        console.error('Error loading vendors and types:', error);
    }
}

// SEO Preview
function updateSEOPreview() {
    const title = $('#skuMetaTitle').val() || $('#skuTitle').val() || 'Product Title';
    const titleVal = $('#skuTitle').val() || '';
    const handle = $('#skuHandle').val() || titleVal.toLowerCase().replace(/\s+/g, '-') || 'product-handle';
    const description = $('#skuMetaDescription').val() || $('#skuDescription').val() || 'Product description will appear here...';
    
    $('#seoPreviewTitle').text(title.substring(0, 70));
    $('#seoPreviewHandle').text(handle);
    $('#seoPreviewDescription').text(description.substring(0, 160));
    
    // Update character counts
    const titleLength = ($('#skuMetaTitle').val() || '').length;
    const descLength = ($('#skuMetaDescription').val() || '').length;
    
    $('#skuMetaTitle').next('.form-text').text(`${titleLength} of 70 characters used`);
    $('#skuMetaDescription').next('.form-text').text(`${descLength} of 160 characters used`);
}

// Track quantity toggle
$('#skuTrackQuantity').on('change', function() {
    if ($(this).is(':checked')) {
        $('#quantitySection').show();
    } else {
        $('#quantitySection').hide();
    }
});

// Shipping toggle
$('#skuRequiresShipping').on('change', function() {
    if ($(this).is(':checked')) {
        $('#shippingDetails').show();
    } else {
        $('#shippingDetails').hide();
    }
});

// Variants management
let productOptions = [];
let selectedSKUImages = [];

function toggleVariants() {
    if ($('#hasVariants').is(':checked')) {
        $('#variantOptions').removeClass('d-none');
        if (productOptions.length === 0) {
            addProductOption();
        }
    } else {
        $('#variantOptions').addClass('d-none');
    }
}

function addProductOption() {
    const optionIndex = productOptions.length;
    const optionHtml = `
        <div class="option-item mb-3" data-option-index="${optionIndex}">
            <div class="row">
                <div class="col-md-3">
                    <input type="text" class="form-control option-name" placeholder="Option name (e.g., Size)" 
                           onchange="updateVariants()">
                </div>
                <div class="col-md-7">
                    <input type="text" class="form-control option-values-input" 
                           placeholder="Option values (comma-separated, e.g., Small, Medium, Large)"
                           onchange="updateVariants()">
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeOption(${optionIndex})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    $('#optionsList').append(optionHtml);
    productOptions.push({ name: '', values: [] });
}

function removeOption(index) {
    $(`.option-item[data-option-index="${index}"]`).remove();
    productOptions.splice(index, 1);
    updateVariants();
}

function updateVariants() {
    // Collect current options
    productOptions = [];
    $('.option-item').each(function() {
        const name = $(this).find('.option-name').val();
        const valuesStr = $(this).find('.option-values-input').val();
        const values = valuesStr.split(',').map(v => v.trim()).filter(v => v);
        
        if (name && values.length > 0) {
            productOptions.push({ name, values });
        }
    });
    
    // Generate variant combinations
    generateVariantCombinations();
}

function generateVariantCombinations() {
    if (productOptions.length === 0) {
        $('#variantsList').empty();
        return;
    }
    
    const combinations = cartesianProduct(productOptions.map(opt => opt.values));
    const tbody = $('#variantsList');
    tbody.empty();
    
    combinations.forEach((combo, index) => {
        const variantTitle = Array.isArray(combo) ? combo.join(' / ') : combo;
        const row = `
            <tr data-variant-index="${index}">
                <td>${variantTitle}</td>
                <td><input type="number" class="form-control form-control-sm variant-price" step="0.01" value="${$('#skuPrice').val()}"></td>
                <td><input type="text" class="form-control form-control-sm variant-sku"></td>
                <td><input type="text" class="form-control form-control-sm variant-barcode"></td>
                <td><input type="number" class="form-control form-control-sm variant-quantity" value="0"></td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeVariant(${index})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

function cartesianProduct(arrays) {
    if (arrays.length === 0) return [];
    if (arrays.length === 1) return arrays[0].map(x => [x]);
    
    const result = [];
    const restProduct = cartesianProduct(arrays.slice(1));
    
    arrays[0].forEach(item => {
        restProduct.forEach(restItem => {
            result.push([item].concat(restItem));
        });
    });
    
    return result;
}

function removeVariant(index) {
    $(`tr[data-variant-index="${index}"]`).remove();
}

function collectProductOptions() {
    return productOptions.map(opt => ({
        name: opt.name,
        values: JSON.stringify(opt.values)
    }));
}

function collectVariantData() {
    const variants = [];
    $('#variantsList tr').each(function() {
        const combo = $(this).find('td:first').text().split(' / ');
        const variant = {
            title: combo.join(' / '),
            price: parseFloat($(this).find('.variant-price').val()) || 0,
            sku_code: $(this).find('.variant-sku').val(),
            barcode: $(this).find('.variant-barcode').val(),
            inventory_quantity: parseInt($(this).find('.variant-quantity').val()) || 0,
        };
        
        // Map options to variant
        productOptions.forEach((opt, index) => {
            if (index === 0) variant.option1 = combo[index];
            if (index === 1) variant.option2 = combo[index];
            if (index === 2) variant.option3 = combo[index];
        });
        
        variants.push(variant);
    });
    return variants;
}

function loadExistingOptions(options) {
    $('#optionsList').empty();
    productOptions = [];
    
    options.forEach(opt => {
        // values is already an array from the API, no need to parse
        const values = Array.isArray(opt.values) ? opt.values : [];
        productOptions.push({ name: opt.name, values: values });
        
        const optionHtml = `
            <div class="option-item mb-3" data-option-index="${productOptions.length - 1}">
                <div class="row">
                    <div class="col-md-3">
                        <input type="text" class="form-control option-name" value="${opt.name}" 
                               placeholder="Option name (e.g., Size)" onchange="updateVariants()">
                    </div>
                    <div class="col-md-7">
                        <input type="text" class="form-control option-values-input" 
                               value="${values.join(', ')}"
                               placeholder="Option values (comma-separated)"
                               onchange="updateVariants()">
                    </div>
                    <div class="col-md-2">
                        <button type="button" class="btn btn-sm btn-outline-danger" 
                                onclick="removeOption(${productOptions.length - 1})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        $('#optionsList').append(optionHtml);
    });
}

function loadExistingVariants(variants) {
    // Variants will be regenerated based on options
    setTimeout(() => {
        // Update variant values
        variants.forEach((variant, index) => {
            const row = $(`tr[data-variant-index="${index}"]`);
            if (row.length) {
                row.find('.variant-price').val(variant.price);
                row.find('.variant-sku').val(variant.sku_code);
                row.find('.variant-barcode').val(variant.barcode);
                row.find('.variant-quantity').val(variant.inventory_quantity);
            }
        });
    }, 100);
}

function loadExistingImages(images) {
    // For now, just load the first image
    if (images.length > 0) {
        const firstImage = images[0];
        selectedSKUImageUrl = firstImage.url;
        displaySKUImagePreviewFromUrl(firstImage.url);
        $('#skuImageUrl').val(firstImage.url);
        $('#skuImageAlt').val(firstImage.alt_text || '');
    }
}

function clearVariants() {
    productOptions = [];
    $('#optionsList').empty();
    $('#variantsList').empty();
    $('#hasVariants').prop('checked', false);
    $('#variantOptions').addClass('d-none');
}