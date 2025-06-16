// Customer Catalog JavaScript - Search and display functionality with filters

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
    
    // Check for pending search from product detail page
    const pendingSearch = sessionStorage.getItem('pendingSearch');
    if (pendingSearch) {
        const searchParams = JSON.parse(pendingSearch);
        sessionStorage.removeItem('pendingSearch');
        
        // Set search text
        if (searchParams.text) {
            document.getElementById('search-text').value = searchParams.text;
            searchQuery = searchParams.text;
        }
        
        // Handle pending image
        if (searchParams.hasImage) {
            const pendingImageData = sessionStorage.getItem('pendingSearchImage');
            if (pendingImageData) {
                sessionStorage.removeItem('pendingSearchImage');
                
                // Convert base64 to blob
                fetch(pendingImageData)
                    .then(res => res.blob())
                    .then(blob => {
                        // Create a File object
                        const file = new File([blob], "search-image.jpg", { type: "image/jpeg" });
                        
                        // Set the search image
                        searchImage = file;
                        
                        // Update preview
                        document.getElementById('preview-img').src = pendingImageData;
                        document.getElementById('image-preview').classList.add('show');
                        
                        // Perform the search
                        performSearch();
                    });
            } else {
                performSearch();
            }
        } else {
            performSearch();
        }
    } else {
        loadProducts();
    }
    
    setupEventListeners();
    loadCompanyLogo();
    initializeFilterToggle();
});

function initializeCatalog() {
    // Load filter options
    loadFilterOptions();
    
    // Setup image upload
    document.getElementById('search-image').addEventListener('change', handleImageUpload);
    
    // Setup search textarea with auto-resize and Enter key handling
    const searchTextarea = document.getElementById('search-text');
    
    // Auto-resize functionality
    searchTextarea.addEventListener('input', autoResizeTextarea);
    
    // Handle Enter key (Shift+Enter for new line, Enter for search)
    searchTextarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            performSearch();
        }
    });
    
    // Initialize resize
    autoResizeTextarea.call(searchTextarea);
    
    // Setup window resize listener for responsive adjustments
    window.addEventListener('resize', debounce(function() {
        autoResizeTextarea.call(searchTextarea);
    }, 250));
    
    // Setup price inputs
    document.getElementById('min-price').addEventListener('input', debounce(applyFilters, 500));
    document.getElementById('max-price').addEventListener('input', debounce(applyFilters, 500));
}

function autoResizeTextarea() {
    // Get screen size for responsive height adjustments
    const screenWidth = window.innerWidth;
    let minHeight = 44; // Default minimum height
    let maxHeight = 120; // Default maximum height
    
    // Adjust heights for smaller screens
    if (screenWidth <= 480) {
        minHeight = 40;
        maxHeight = 80;
        this.style.height = '40px';
    } else if (screenWidth <= 360) {
        minHeight = 36;
        maxHeight = 72;
        this.style.height = '36px';
    } else {
        this.style.height = '44px';
    }
    
    // Calculate the new height based on content
    const scrollHeight = this.scrollHeight;
    const newHeight = Math.max(minHeight, Math.min(maxHeight, scrollHeight));
    
    // Set the new height
    this.style.height = newHeight + 'px';
    
    // Handle overflow visibility
    if (scrollHeight > minHeight) {
        this.classList.add('expanded');
        // Only show scrollbar if content exceeds max height
        if (scrollHeight > maxHeight) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
    } else {
        this.classList.remove('expanded');
        this.style.overflowY = 'hidden';
    }
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

async function loadProducts(page = 1) {
    showLoading();
    currentPage = page;
    
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            sort: currentSort
        });
        
        // Add search query if present
        if (searchQuery) {
            params.append('q', searchQuery);
        }
        
        // Add filters
        if (currentFilters.categories.length > 0) {
            currentFilters.categories.forEach(cat => params.append('categories', cat));
        }
        
        if (currentFilters.vendors.length > 0) {
            currentFilters.vendors.forEach(vendor => params.append('vendors', vendor));
        }
        
        if (currentFilters.productTypes.length > 0) {
            currentFilters.productTypes.forEach(type => params.append('product_types', type));
        }
        
        if (currentFilters.minPrice !== null) {
            params.append('min_price', currentFilters.minPrice);
        }
        
        if (currentFilters.maxPrice !== null) {
            params.append('max_price', currentFilters.maxPrice);
        }
        
        // Add stock filter
        let stockFilter = 'all';
        if (currentFilters.inStock && !currentFilters.outOfStock) {
            stockFilter = 'in_stock';
        } else if (!currentFilters.inStock && currentFilters.outOfStock) {
            stockFilter = 'out_of_stock';
        }
        params.append('stock', stockFilter);
        
        const response = await fetch(`/api/catalog/products?${params}`);
        const data = await response.json();
        
        if (data.products) {
            allProducts = data.products;
            filteredProducts = [...allProducts];
            displayProducts(filteredProducts);
            updateResultsCount(data.total || filteredProducts.length);
            updatePagination(data.page || 1, data.total_pages || 1, data.total || filteredProducts.length);
        } else {
            showNoResults();
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading products:', error);
        showNoResults();
        hideLoading();
    }
}

function displayProducts(products) {
    const container = document.getElementById('products-container');
    const isListView = currentView === 'list';
    
    // Update container class
    container.className = isListView ? 'products-list' : 'products-grid';
    
    if (products.length === 0) {
        showNoResults();
        return;
    }
    
    hideNoResults();
    
    container.innerHTML = products.map(product => {
        const imageUrl = product.images && product.images.length > 0 
            ? product.images[0].url 
            : '/static/images/placeholder.svg';
            
        const vendor = product.vendor || 'Unknown';
        const price = parseFloat(product.price) || 0;
        const formattedPrice = price.toFixed(2);
        
        // Get product options for display
        const options = product.variants && product.variants.length > 0
            ? product.variants.slice(0, 3).map(v => v.option1 || v.option2 || v.option3).filter(Boolean)
            : [];
            
        return `
            <div class="product-card" data-product-id="${product.id}" onclick="viewProduct(${product.id})">
                <img src="${imageUrl}" alt="${product.title}" class="product-image" 
                     onerror="this.src='/static/images/placeholder.svg'">
                <div class="product-info">
                    <h3 class="product-title">${product.title}</h3>
                    <p class="product-vendor">${vendor}</p>
                    <div class="product-price">
                        <span class="current-price">$${formattedPrice}</span>
                    </div>
                    ${options.length > 0 ? `
                        <div class="product-options">
                            ${options.map(option => `<span class="option-badge">${option}</span>`).join('')}
                        </div>
                    ` : ''}
                    <div class="product-actions">
                        <button class="add-to-cart-btn" onclick="event.stopPropagation(); addToCart(${product.id})">
                            <i class="fas fa-shopping-cart"></i>
                            <span class="btn-text">Add to Cart</span>
                        </button>
                        <button class="quick-view-btn" onclick="event.stopPropagation(); quickView(${product.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function performSearch() {
    const textQuery = document.getElementById('search-text').value.trim();
    const imageFile = searchImage;
    
    if (!textQuery && !imageFile) {
        // If no search terms, reload all products
        searchQuery = '';
        searchImage = null;
        loadProducts(1);
        return;
    }
    
    showLoading();
    searchQuery = textQuery;
    
    try {
        const formData = new FormData();
        
        if (imageFile) {
            formData.append('type', 'image');
            formData.append('image', imageFile);
            if (textQuery) {
                formData.append('text_query', textQuery);
            }
        } else {
            formData.append('type', 'text');
            formData.append('query', textQuery);
        }
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.results) {
            allProducts = data.results;
            filteredProducts = [...allProducts];
            displayProducts(filteredProducts);
            updateResultsCount(filteredProducts.length);
            updatePagination(1, 1, filteredProducts.length);
            currentPage = 1;
        } else {
            showNoResults();
        }
        
        hideLoading();
    } catch (error) {
        console.error('Search error:', error);
        showNoResults();
        hideLoading();
    }
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.type.startsWith('image/')) {
            if (file.size > 16 * 1024 * 1024) { // 16MB limit
                alert('Image file is too large. Please select an image under 16MB.');
                return;
            }
            
            searchImage = file;
            
            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('preview-img').src = e.target.result;
                document.getElementById('image-preview').classList.add('show');
            };
            reader.readAsDataURL(file);
        } else {
            alert('Please select a valid image file (JPG, PNG, GIF, WEBP)');
        }
    }
}

function removeImage() {
    searchImage = null;
    document.getElementById('search-image').value = '';
    document.getElementById('image-preview').classList.remove('show');
}

function applySort() {
    currentSort = document.getElementById('sort-select').value;
    
    // Sort the current filtered products
    switch (currentSort) {
        case 'price-low':
            filteredProducts.sort((a, b) => (parseFloat(a.price) || 0) - (parseFloat(b.price) || 0));
            break;
        case 'price-high':
            filteredProducts.sort((a, b) => (parseFloat(b.price) || 0) - (parseFloat(a.price) || 0));
            break;
        case 'name-asc':
            filteredProducts.sort((a, b) => a.title.localeCompare(b.title));
            break;
        case 'name-desc':
            filteredProducts.sort((a, b) => b.title.localeCompare(a.title));
            break;
        case 'newest':
            filteredProducts.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
            break;
        default: // relevance
            // Keep original order
            break;
    }
    
    displayProducts(filteredProducts);
}

function setView(view) {
    currentView = view;
    
    // Update view toggle buttons
    document.querySelectorAll('.view-toggle').forEach(btn => btn.classList.remove('active'));
    event.target.closest('.view-toggle').classList.add('active');
    
    // Update display
    displayProducts(filteredProducts);
}

function updateResultsCount(total) {
    document.getElementById('results-count').textContent = total;
}

function updatePagination(currentPage, totalPages, totalItems) {
    const container = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    paginationHTML += `
        <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} 
                onclick="loadProducts(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i>
        </button>
    `;
    
    // Page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Adjust start if we're near the end
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // First page and ellipsis
    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="loadProducts(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
    }
    
    // Page numbers
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <button class="page-btn ${i === currentPage ? 'active' : ''}" 
                    onclick="loadProducts(${i})">${i}</button>
        `;
    }
    
    // Last page and ellipsis
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="page-btn" onclick="loadProducts(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    paginationHTML += `
        <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} 
                onclick="loadProducts(${currentPage + 1})">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    container.innerHTML = paginationHTML;
}

// Utility functions
function showLoading() {
    document.getElementById('loading').classList.add('show');
    hideNoResults();
}

function hideLoading() {
    document.getElementById('loading').classList.remove('show');
}

function showNoResults() {
    document.getElementById('no-results').classList.add('show');
}

function hideNoResults() {
    document.getElementById('no-results').classList.remove('show');
}

// Product interaction functions
function viewProduct(productId) {
    window.location.href = `/product/${productId}`;
}

// addToCart function is now provided by cart.js

function quickView(productId) {
    // Implement quick view functionality
    console.log('Quick view:', productId);
    // You can implement modal quick view here
    alert('Quick view coming soon!');
}

// Filter Functions
async function loadFilterOptions() {
    try {
        const response = await fetch('/api/catalog/filters');
        const data = await response.json();
        
        // Populate categories
        populateFilterSection('categories-filter', data.categories, 'categories');
        
        // Populate vendors
        populateFilterSection('vendors-filter', data.vendors, 'vendors');
        
        // Populate product types
        populateFilterSection('product-types-filter', data.productTypes, 'productTypes');
        
        // Populate options
        populateOptionsFilter(data.options);
        
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

function toggleFilter(element) {
    const content = element.nextElementSibling;
    const icon = element.querySelector('i');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        element.classList.remove('collapsed');
        icon.style.transform = 'rotate(0deg)';
    } else {
        content.classList.add('collapsed');
        element.classList.add('collapsed');
        icon.style.transform = 'rotate(-90deg)';
    }
}

function applyFilters() {
    // Get price range
    const minPrice = parseFloat(document.getElementById('min-price').value) || null;
    const maxPrice = parseFloat(document.getElementById('max-price').value) || null;
    
    currentFilters.minPrice = minPrice;
    currentFilters.maxPrice = maxPrice;
    
    // Apply filters to current products
    loadProducts(1);
}

// Filter Toggle Functions
let filtersVisible = true;

function initializeFilterToggle() {
    // Check screen size and auto-hide filters on medium/small screens
    if (window.innerWidth <= 1024) {
        hideFilters();
    }
    
    // Setup resize listener for auto-hide functionality
    window.addEventListener('resize', debounce(function() {
        if (window.innerWidth <= 1024) {
            hideFilters();
        } else {
            showFilters();
        }
    }, 250));
}

function toggleFilters() {
    if (filtersVisible) {
        hideFilters();
    } else {
        showFilters();
    }
}

function showFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const toggleIcon = document.getElementById('filter-toggle-icon');
    const isMobile = window.innerWidth <= 1024;
    
    filtersVisible = true;
    
    if (isMobile) {
        sidebar.classList.add('show-mobile');
    } else {
        sidebar.classList.remove('collapsed');
    }
    
    // Hide the small toggle icon when filters are visible
    toggleIcon.classList.remove('visible');
}

function hideFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const toggleIcon = document.getElementById('filter-toggle-icon');
    const isMobile = window.innerWidth <= 1024;
    
    filtersVisible = false;
    
    if (isMobile) {
        sidebar.classList.remove('show-mobile');
    } else {
        sidebar.classList.add('collapsed');
    }
    
    // Show the small toggle icon when filters are hidden
    toggleIcon.classList.add('visible');
}

// Company Logo Functions
function loadCompanyLogo() {
    // Load saved logo from API endpoint
    fetch('/api/settings/logo')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('No logo found');
        })
        .then(data => {
            if (data.logo_url) {
                document.getElementById('logo-img').src = data.logo_url;
            }
        })
        .catch(error => {
            console.log('No company logo set yet');
        });
}

// Debounce utility
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