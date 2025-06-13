// Catalog JavaScript - Advanced search and filtering functionality

let currentPage = 1;
let currentFilters = {
    categories: [],
    vendors: [],
    productTypes: [],
    options: {},
    minPrice: null,
    maxPrice: null,
    inStock: true,
    outOfStock: false
};
let currentSort = 'relevance';
let currentView = 'grid';
let searchQuery = '';
let searchImage = null;
let allProducts = [];
let filteredProducts = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCatalog();
    loadProducts();
    setupEventListeners();
});

function initializeCatalog() {
    // Load filter options
    loadFilterOptions();
    
    // Setup image upload
    document.getElementById('search-image').addEventListener('change', handleImageUpload);
    
    // Setup price inputs
    document.getElementById('min-price').addEventListener('input', debounce(applyFilters, 500));
    document.getElementById('max-price').addEventListener('input', debounce(applyFilters, 500));
    
    // Setup search input
    document.getElementById('search-text').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

function setupEventListeners() {
    // In stock checkbox
    document.getElementById('in-stock').addEventListener('change', function() {
        currentFilters.inStock = this.checked;
        applyFilters();
    });
    
    // Out of stock checkbox
    document.getElementById('out-of-stock').addEventListener('change', function() {
        currentFilters.outOfStock = this.checked;
        applyFilters();
    });
}

async function loadFilterOptions() {
    try {
        console.log('Loading filter options...');
        const response = await fetch('/api/catalog/filters');
        console.log('Filter response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Filter data:', data);
        
        // Populate categories
        if (data.categories) {
            populateFilterSection('categories-filter', data.categories, 'categories');
        } else {
            document.getElementById('categories-filter').innerHTML = '<p style="color: #999; font-size: 14px;">No categories found</p>';
        }
        
        // Populate vendors
        if (data.vendors) {
            populateFilterSection('vendors-filter', data.vendors, 'vendors');
        } else {
            document.getElementById('vendors-filter').innerHTML = '<p style="color: #999; font-size: 14px;">No brands found</p>';
        }
        
        // Populate product types
        if (data.productTypes) {
            populateFilterSection('product-types-filter', data.productTypes, 'productTypes');
        } else {
            document.getElementById('product-types-filter').innerHTML = '<p style="color: #999; font-size: 14px;">No product types found</p>';
        }
        
        // Populate options
        if (data.options) {
            populateOptionsFilter(data.options);
        }
        
        // Set price range
        if (data.priceRange) {
            document.getElementById('min-price').placeholder = `Min ($${data.priceRange.min})`;
            document.getElementById('max-price').placeholder = `Max ($${data.priceRange.max})`;
        }
        
        console.log('Filter options loaded successfully');
    } catch (error) {
        console.error('Error loading filter options:', error);
        // Show error message in filters
        document.getElementById('categories-filter').innerHTML = '<p style="color: #dc3545; font-size: 14px;">Error loading filters</p>';
        document.getElementById('vendors-filter').innerHTML = '<p style="color: #dc3545; font-size: 14px;">Error loading filters</p>';
        document.getElementById('product-types-filter').innerHTML = '<p style="color: #dc3545; font-size: 14px;">Error loading filters</p>';
    }
}

function populateFilterSection(containerId, items, filterKey) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'filter-option';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `${filterKey}-${item.value}`;
        checkbox.value = item.value;
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                currentFilters[filterKey].push(item.value);
            } else {
                currentFilters[filterKey] = currentFilters[filterKey].filter(v => v !== item.value);
            }
            applyFilters();
        });
        
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.innerHTML = `${item.name} <span class="filter-count">(${item.count})</span>`;
        
        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
}

function populateOptionsFilter(options) {
    const container = document.getElementById('options-filter');
    container.innerHTML = '';
    
    Object.entries(options).forEach(([optionName, values]) => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'filter-subsection';
        
        const title = document.createElement('div');
        title.className = 'filter-subtitle';
        title.textContent = optionName;
        optionDiv.appendChild(title);
        
        values.forEach(value => {
            const div = document.createElement('div');
            div.className = 'filter-option';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `option-${optionName}-${value.value}`;
            checkbox.value = value.value;
            checkbox.addEventListener('change', function() {
                if (!currentFilters.options[optionName]) {
                    currentFilters.options[optionName] = [];
                }
                
                if (this.checked) {
                    currentFilters.options[optionName].push(value.value);
                } else {
                    currentFilters.options[optionName] = currentFilters.options[optionName].filter(v => v !== value.value);
                    if (currentFilters.options[optionName].length === 0) {
                        delete currentFilters.options[optionName];
                    }
                }
                applyFilters();
            });
            
            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.innerHTML = `${value.value} <span class="filter-count">(${value.count})</span>`;
            
            div.appendChild(checkbox);
            div.appendChild(label);
            optionDiv.appendChild(div);
        });
        
        container.appendChild(optionDiv);
    });
}

async function loadProducts(page = 1) {
    showLoading();
    currentPage = page;
    
    try {
        const params = buildSearchParams();
        console.log('Loading products with params:', params);
        
        const response = await fetch(`/api/catalog/products?${params}`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        allProducts = data.products || [];
        filteredProducts = allProducts;
        
        displayProducts(allProducts);
        updateResultsCount(data.total || allProducts.length);
        updatePagination(data.total || allProducts.length, data.per_page || 20, data.page || 1);
        updateActiveFilters();
        
    } catch (error) {
        console.error('Error loading products:', error);
        showError();
    } finally {
        hideLoading();
    }
}

function buildSearchParams() {
    const params = new URLSearchParams();
    
    // Add search query
    if (searchQuery) {
        params.append('q', searchQuery);
    }
    
    // Add filters
    if (currentFilters.categories.length > 0) {
        params.append('categories', currentFilters.categories.join(','));
    }
    
    if (currentFilters.vendors.length > 0) {
        params.append('vendors', currentFilters.vendors.join(','));
    }
    
    if (currentFilters.productTypes.length > 0) {
        params.append('product_types', currentFilters.productTypes.join(','));
    }
    
    // Add options filters
    Object.entries(currentFilters.options).forEach(([key, values]) => {
        if (values.length > 0) {
            params.append(`option_${key}`, values.join(','));
        }
    });
    
    // Add price range
    if (currentFilters.minPrice) {
        params.append('min_price', currentFilters.minPrice);
    }
    
    if (currentFilters.maxPrice) {
        params.append('max_price', currentFilters.maxPrice);
    }
    
    // Add stock filters
    if (!currentFilters.inStock && currentFilters.outOfStock) {
        params.append('stock', 'out_of_stock');
    } else if (currentFilters.inStock && !currentFilters.outOfStock) {
        params.append('stock', 'in_stock');
    }
    
    // Add sort
    params.append('sort', currentSort);
    
    // Add pagination
    params.append('page', currentPage);
    
    return params.toString();
}

async function performSearch() {
    searchQuery = document.getElementById('search-text').value;
    
    // Check if we have both text and image
    if (searchQuery && searchImage) {
        // Combined search using vector search
        await performCombinedSearch();
    } else if (searchImage) {
        // Image only search using vector search
        await performImageSearch();
    } else if (searchQuery) {
        // Text search now uses hybrid vector + database search with filters
        loadProducts(1);
    }
}

async function performVectorTextSearch() {
    showLoading();
    
    try {
        // Validate that we have a search query
        if (!searchQuery.trim()) {
            alert('Please enter a search query.');
            hideLoading();
            return;
        }
        
        const formData = new FormData();
        formData.append('query', searchQuery);
        formData.append('search_type', 'text');
        
        // Add filters to form data
        formData.append('filters', JSON.stringify(currentFilters));
        formData.append('sort', currentSort);
        formData.append('page', currentPage);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error performing vector text search: ' + data.error);
            return;
        }
        
        // SearchResource returns results, not products
        const products = data.results || [];
        displayProducts(products);
        updateResultsCount(products.length);
        updateActiveFilters();
        
    } catch (error) {
        console.error('Error performing vector text search:', error);
        showError();
    } finally {
        hideLoading();
    }
}

async function performImageSearch() {
    showLoading();
    
    try {
        // Validate that we have an image
        if (!searchImage) {
            alert('Please upload an image to search with.');
            hideLoading();
            return;
        }
        
        const formData = new FormData();
        formData.append('image', searchImage);
        formData.append('search_type', 'image');
        
        // Add filters to form data
        formData.append('filters', JSON.stringify(currentFilters));
        formData.append('sort', currentSort);
        formData.append('page', currentPage);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error performing image search: ' + data.error);
            return;
        }
        
        // SearchResource returns results, not products
        const products = data.results || [];
        displayProducts(products);
        updateResultsCount(products.length);
        updateActiveFilters();
        
    } catch (error) {
        console.error('Error performing image search:', error);
        showError();
    } finally {
        hideLoading();
    }
}

async function performCombinedSearch() {
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('query', searchQuery);
        formData.append('image', searchImage);
        formData.append('search_type', 'text_image');
        
        // Add filters
        formData.append('filters', JSON.stringify(currentFilters));
        formData.append('sort', currentSort);
        formData.append('page', currentPage);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error performing search: ' + data.error);
            return;
        }
        
        // SearchResource returns results, not products
        const products = data.results || [];
        displayProducts(products);
        updateResultsCount(products.length);
        updateActiveFilters();
        
    } catch (error) {
        console.error('Error performing combined search:', error);
        showError();
    } finally {
        hideLoading();
    }
}

function displayProducts(products) {
    const container = document.getElementById('products-container');
    container.innerHTML = '';
    container.className = currentView === 'grid' ? 'products-grid' : 'products-list';
    
    if (products.length === 0) {
        document.getElementById('no-results').classList.add('show');
        return;
    } else {
        document.getElementById('no-results').classList.remove('show');
    }
    
    products.forEach(product => {
        const productCard = createProductCard(product);
        container.appendChild(productCard);
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.dataset.productId = product.id;
    card.onclick = () => viewProductDetails(product.id);
    
    // Get main image
    const imageUrl = product.images && product.images.length > 0 
        ? product.images[0].url 
        : '/static/images/placeholder.svg';
    
    // Get price info
    const currentPrice = product.price || 0;
    const comparePrice = product.compare_at_price;
    
    // Get options
    const options = product.options || [];
    
    // Escape HTML to prevent XSS
    const safeTitle = escapeHtml(product.title || 'Unknown Product');
    const safeVendor = escapeHtml(product.vendor || 'Unknown Vendor');
    
    card.innerHTML = `
        <img src="${imageUrl}" alt="${safeTitle}" class="product-image" onerror="this.src='/static/images/placeholder.svg'">
        <div class="product-info">
            <h3 class="product-title">${safeTitle}</h3>
            <div class="product-vendor">${safeVendor}</div>
            <div class="product-price">
                <span class="current-price">$${parseFloat(currentPrice).toFixed(2)}</span>
                ${comparePrice && parseFloat(comparePrice) > parseFloat(currentPrice) ? 
                    `<span class="original-price">$${parseFloat(comparePrice).toFixed(2)}</span>` : ''}
            </div>
            ${options.length > 0 ? `
                <div class="product-options">
                    ${options.map(opt => `
                        <span class="option-badge">${escapeHtml(opt.name)}: ${opt.values ? opt.values.length : 0} options</span>
                    `).join('')}
                </div>
            ` : ''}
            <div class="product-actions">
                <button class="add-to-cart-btn" onclick="event.stopPropagation(); addToCart(${product.id})">
                    <i class="fas fa-shopping-cart"></i> <span class="btn-text">Add to Cart</span>
                </button>
                <button class="quick-view-btn" onclick="event.stopPropagation(); quickView(${product.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function updateResultsCount(count) {
    document.getElementById('results-count').textContent = count;
}

function updatePagination(total, perPage, currentPage) {
    const totalPages = Math.ceil(total / perPage);
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    if (totalPages <= 1) return;
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => loadProducts(currentPage - 1);
    pagination.appendChild(prevBtn);
    
    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => loadProducts(i);
        pagination.appendChild(pageBtn);
    }
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => loadProducts(currentPage + 1);
    pagination.appendChild(nextBtn);
}

function updateActiveFilters() {
    const container = document.getElementById('active-filters');
    const hasFilters = currentFilters.categories.length > 0 || 
                      currentFilters.vendors.length > 0 || 
                      currentFilters.productTypes.length > 0 ||
                      Object.keys(currentFilters.options).length > 0 ||
                      currentFilters.minPrice || currentFilters.maxPrice ||
                      searchQuery || searchImage;
    
    if (!hasFilters) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    container.innerHTML = '';
    
    // Add search query pill
    if (searchQuery) {
        const pill = createFilterPill('Search', searchQuery, () => {
            document.getElementById('search-text').value = '';
            searchQuery = '';
            loadProducts(1);
        });
        container.appendChild(pill);
    }
    
    // Add image search pill
    if (searchImage) {
        const pill = createFilterPill('Image', 'Image uploaded', () => {
            removeImage();
            loadProducts(1);
        });
        container.appendChild(pill);
    }
    
    // Add category pills
    currentFilters.categories.forEach(cat => {
        const pill = createFilterPill('Category', cat, () => {
            currentFilters.categories = currentFilters.categories.filter(c => c !== cat);
            document.getElementById(`categories-${cat}`).checked = false;
            applyFilters();
        });
        container.appendChild(pill);
    });
    
    // Add vendor pills
    currentFilters.vendors.forEach(vendor => {
        const pill = createFilterPill('Vendor', vendor, () => {
            currentFilters.vendors = currentFilters.vendors.filter(v => v !== vendor);
            document.getElementById(`vendors-${vendor}`).checked = false;
            applyFilters();
        });
        container.appendChild(pill);
    });
    
    // Add price range pill
    if (currentFilters.minPrice || currentFilters.maxPrice) {
        const priceText = `$${currentFilters.minPrice || '0'} - $${currentFilters.maxPrice || '∞'}`;
        const pill = createFilterPill('Price', priceText, () => {
            currentFilters.minPrice = null;
            currentFilters.maxPrice = null;
            document.getElementById('min-price').value = '';
            document.getElementById('max-price').value = '';
            applyFilters();
        });
        container.appendChild(pill);
    }
    
    // Add clear all button
    const clearBtn = document.createElement('button');
    clearBtn.className = 'clear-all-filters';
    clearBtn.textContent = 'Clear All';
    clearBtn.onclick = clearAllFilters;
    container.appendChild(clearBtn);
}

function createFilterPill(type, value, removeCallback) {
    const pill = document.createElement('div');
    pill.className = 'filter-pill';
    pill.innerHTML = `
        <span>${type}: ${value}</span>
        <button onclick="event.stopPropagation()">
            <i class="fas fa-times"></i>
        </button>
    `;
    pill.querySelector('button').onclick = removeCallback;
    return pill;
}

function clearAllFilters() {
    // Reset all filters
    currentFilters = {
        categories: [],
        vendors: [],
        productTypes: [],
        options: {},
        minPrice: null,
        maxPrice: null,
        inStock: true,
        outOfStock: false
    };
    
    // Clear search
    searchQuery = '';
    document.getElementById('search-text').value = '';
    removeImage();
    
    // Uncheck all filter checkboxes
    document.querySelectorAll('.filter-option input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    
    // Reset stock checkboxes
    document.getElementById('in-stock').checked = true;
    document.getElementById('out-of-stock').checked = false;
    
    // Clear price inputs
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    
    // Reload products
    loadProducts(1);
}

function applyFilters() {
    // Update price filters
    currentFilters.minPrice = document.getElementById('min-price').value || null;
    currentFilters.maxPrice = document.getElementById('max-price').value || null;
    
    loadProducts(1);
}

function applySort() {
    currentSort = document.getElementById('sort-select').value;
    loadProducts(currentPage);
}

function setView(view) {
    currentView = view;
    
    // Update toggle buttons
    document.querySelectorAll('.view-toggle').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.closest('.view-toggle').classList.add('active');
    
    // Re-display products
    displayProducts(filteredProducts);
}

function toggleFilter(element) {
    element.classList.toggle('collapsed');
    element.nextElementSibling.classList.toggle('collapsed');
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        searchImage = file;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview-img').src = e.target.result;
            document.getElementById('image-preview').classList.add('show');
        };
        reader.readAsDataURL(file);
        
        // Automatically perform search when image is uploaded
        // Small delay to ensure image preview is shown first
        setTimeout(() => {
            performSearch();
        }, 100);
    }
}

function removeImage() {
    searchImage = null;
    document.getElementById('search-image').value = '';
    document.getElementById('image-preview').classList.remove('show');
}

function viewProductDetails(productId) {
    // Navigate to product detail page
    console.log('Navigating to product:', productId);
    window.location.href = `/product/${productId}`;
}

// Utility function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, function(m) { return map[m]; });
}

// addToCart function is provided by cart.js

async function quickView(productId) {
    try {
        const response = await fetch(`/api/products/${productId}`);
        const product = await response.json();
        
        const modalBody = document.getElementById('quick-view-content');
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <img src="${product.images?.[0]?.url || '/static/images/placeholder.svg'}" 
                         class="img-fluid" alt="${product.title}">
                </div>
                <div class="col-md-6">
                    <h3>${product.title}</h3>
                    <p class="text-muted">${product.vendor || 'Unknown Vendor'}</p>
                    <div class="mb-3">
                        <span class="h4 text-primary">$${product.price}</span>
                        ${product.compare_at_price ? 
                            `<span class="text-muted text-decoration-line-through ms-2">$${product.compare_at_price}</span>` 
                            : ''}
                    </div>
                    <p>${product.description || 'No description available'}</p>
                    ${product.options?.length > 0 ? `
                        <div class="mb-3">
                            <h5>Options:</h5>
                            ${product.options.map(opt => `
                                <div class="mb-2">
                                    <strong>${opt.name}:</strong> ${opt.values.join(', ')}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    <button class="btn btn-primary w-100" onclick="addToCart(${product.id})">
                        <i class="fas fa-shopping-cart"></i> <span class="btn-text">Add to Cart</span>
                    </button>
                </div>
            </div>
        `;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading product details:', error);
        alert('Error loading product details');
    }
}

function showLoading() {
    document.getElementById('loading').classList.add('show');
    document.getElementById('products-container').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').classList.remove('show');
    document.getElementById('products-container').style.display = '';
}

function showError() {
    hideLoading();
    alert('Error loading products. Please try again.');
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}