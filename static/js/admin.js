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
    }
}

async function deleteCategory(id) {
    if (!confirm('Are you sure you want to delete this category?')) return;
    
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
    $('#skuModalTitle').text('Add SKU');
    $('#skuForm')[0].reset();
    $('#skuId').val('');
    clearSKUImage();
    loadCategoriesForDropdowns(); // Load categories for dropdown
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
    try {
        const sku = await apiCall(`/skus/${id}`);
        await loadCategoriesForDropdowns(); // Load categories for dropdown
        
        $('#skuModalTitle').text('Edit SKU');
        $('#skuId').val(sku.id);
        $('#skuTitle').val(sku.title);
        $('#skuCode').val(sku.sku_code);
        $('#skuDescription').val(sku.description);
        $('#skuPrice').val(sku.price);
        $('#skuVendor').val(sku.vendor);
        $('#skuProductType').val(sku.product_type);
        $('#skuTags').val(sku.tags);
        $('#skuQuantity').val(sku.quantity || 0);
        $('#skuWeight').val(sku.weight || 0);
        
        // Set selected categories
        const categoryIds = sku.categories.map(cat => cat.id);
        $('#skuCategories').val(categoryIds);
        
        // Load existing image if available
        clearSKUImage(); // Clear any previous selection
        if (sku.images && sku.images.length > 0) {
            const existingImage = sku.images[0];
            selectedSKUImageUrl = existingImage.url;
            displaySKUImagePreviewFromUrl(existingImage.url);
            $('#skuImageUrl').val(existingImage.url);
        }
        
        $('#skuModal').modal('show');
    } catch (error) {
        showToast('Failed to load SKU', 'error');
    }
}

async function saveSKU() {
    const id = $('#skuId').val();
    
    // Prepare form data for potential file upload
    const formData = new FormData();
    formData.append('title', $('#skuTitle').val());
    formData.append('sku_code', $('#skuCode').val());
    formData.append('description', $('#skuDescription').val());
    formData.append('price', parseFloat($('#skuPrice').val()) || 0);
    formData.append('vendor', $('#skuVendor').val());
    formData.append('product_type', $('#skuProductType').val());
    formData.append('tags', $('#skuTags').val());
    formData.append('quantity', parseInt($('#skuQuantity').val()) || 0);
    formData.append('weight', parseFloat($('#skuWeight').val()) || 0);
    
    // Add category IDs
    const categoryIds = $('#skuCategories').val();
    if (categoryIds && categoryIds.length > 0) {
        categoryIds.forEach(catId => {
            formData.append('category_ids', parseInt(catId));
        });
    }
    
    // Add image if selected
    if (selectedSKUImage) {
        formData.append('image', selectedSKUImage);
    } else if (selectedSKUImageUrl) {
        formData.append('image_url', selectedSKUImageUrl);
    }
    
    try {
        let response;
        if (id) {
            // For updates, check if we have an image to upload
            if (selectedSKUImage || selectedSKUImageUrl) {
                // Use multipart form data for image upload
                const formData = new FormData();
                formData.append('title', $('#skuTitle').val());
                formData.append('sku_code', $('#skuCode').val());
                formData.append('description', $('#skuDescription').val());
                formData.append('price', parseFloat($('#skuPrice').val()) || 0);
                formData.append('vendor', $('#skuVendor').val());
                formData.append('product_type', $('#skuProductType').val());
                formData.append('tags', $('#skuTags').val());
                formData.append('quantity', parseInt($('#skuQuantity').val()) || 0);
                formData.append('weight', parseFloat($('#skuWeight').val()) || 0);
                
                // Add category IDs
                if (categoryIds && categoryIds.length > 0) {
                    categoryIds.forEach(catId => {
                        formData.append('category_ids', parseInt(catId));
                    });
                }
                
                // Add image
                if (selectedSKUImage) {
                    formData.append('image', selectedSKUImage);
                } else if (selectedSKUImageUrl) {
                    formData.append('image_url', selectedSKUImageUrl);
                }
                
                console.log('Sending form data with image for update');
                response = await fetch(`/api/skus/${id}`, {
                    method: 'PUT',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Failed to update SKU');
                }
                response = await response.json();
            } else {
                // Use regular JSON API for updates without images
                const data = {
                    title: $('#skuTitle').val(),
                    sku_code: $('#skuCode').val(),
                    description: $('#skuDescription').val(),
                    price: parseFloat($('#skuPrice').val()) || 0,
                    vendor: $('#skuVendor').val(),
                    product_type: $('#skuProductType').val(),
                    tags: $('#skuTags').val(),
                    quantity: parseInt($('#skuQuantity').val()) || 0,
                    weight: parseFloat($('#skuWeight').val()) || 0,
                    category_ids: categoryIds ? categoryIds.map(id => parseInt(id)) : []
                };
                
                console.log('Sending JSON data for update (no image)');
                response = await apiCall(`/skus/${id}`, 'PUT', data);
            }
            showToast('SKU updated successfully');
        } else {
            // For new SKUs, check if we have an image
            if (selectedSKUImage || selectedSKUImageUrl) {
                // Use multipart form data for image upload
                response = await fetch('/api/skus', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Failed to create SKU');
                }
                response = await response.json();
            } else {
                // Use regular JSON API
                const data = {
                    title: $('#skuTitle').val(),
                    sku_code: $('#skuCode').val(),
                    description: $('#skuDescription').val(),
                    price: parseFloat($('#skuPrice').val()) || 0,
                    vendor: $('#skuVendor').val(),
                    product_type: $('#skuProductType').val(),
                    tags: $('#skuTags').val(),
                    quantity: parseInt($('#skuQuantity').val()) || 0,
                    weight: parseFloat($('#skuWeight').val()) || 0,
                    category_ids: categoryIds ? categoryIds.map(id => parseInt(id)) : []
                };
                response = await apiCall('/skus', 'POST', data);
            }
            showToast('SKU created successfully');
        }
        
        $('#skuModal').modal('hide');
        clearSKUImage(); // Clear image selection
        
        // Refresh the SKU list if it's currently displayed
        const contentFrame = document.getElementById('contentFrame');
        if (contentFrame.src.includes('/admin/skus')) {
            contentFrame.contentWindow.loadSKUs();
        }
    } catch (error) {
        console.error('Error saving SKU:', error);
        showToast('Failed to save SKU', 'error');
    }
}

async function deleteSKU(id) {
    if (!confirm('Are you sure you want to delete this SKU?')) return;
    
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