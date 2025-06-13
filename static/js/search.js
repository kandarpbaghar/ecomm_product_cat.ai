// Search functionality
let selectedFile = null;
let selectedCombinedFile = null;

// Text search
async function performTextSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('searchQuery').value.trim();
    if (!query) return;
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('type', 'text');
        formData.append('query', query);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        displayResults(data.results || []);
    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

// Image search
async function performImageSearch(event) {
    event.preventDefault();
    
    if (!selectedFile) {
        showToast('Please select an image first', 'error');
        return;
    }
    
    // Validate file
    const validationError = validateImageFile(selectedFile);
    if (validationError) {
        showToast(validationError, 'error');
        return;
    }
    
    showLoading();
    const resetProgress = showImageUploadProgress();
    
    try {
        const formData = new FormData();
        formData.append('type', 'image');
        formData.append('image', selectedFile);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayResults(data.results || []);
        
        if (data.results && data.results.length > 0) {
            showToast(`Found ${data.results.length} similar products!`, 'success');
        } else {
            showToast('No similar products found. Try a different image.', 'info');
        }
        
    } catch (error) {
        console.error('Search error:', error);
        showToast(`Search failed: ${error.message}`, 'error');
    } finally {
        hideLoading();
        resetProgress();
    }
}

// Combined text + image search
async function performCombinedSearch(event) {
    event.preventDefault();
    
    const query = document.getElementById('combinedSearchQuery').value.trim();
    const hasImage = selectedCombinedFile !== null;
    
    if (!query && !hasImage) {
        showToast('Please provide either search text or an image', 'error');
        return;
    }
    
    // Validate image if provided
    if (hasImage) {
        const validationError = validateImageFile(selectedCombinedFile);
        if (validationError) {
            showToast(validationError, 'error');
            return;
        }
    }
    
    showLoading();
    const resetProgress = showCombinedSearchProgress();
    
    try {
        const formData = new FormData();
        formData.append('type', 'text_image');
        
        if (query) {
            formData.append('query', query);
        }
        
        if (hasImage) {
            formData.append('image', selectedCombinedFile);
        }
        
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayResults(data.results || []);
        
        if (data.results && data.results.length > 0) {
            const searchType = query && hasImage ? 'text + image' : query ? 'text' : 'image';
            showToast(`Found ${data.results.length} products using ${searchType} search!`, 'success');
        } else {
            showToast('No matching products found. Try different text or image.', 'info');
        }
        
    } catch (error) {
        console.error('Combined search error:', error);
        showToast(`Search failed: ${error.message}`, 'error');
    } finally {
        hideLoading();
        resetProgress();
    }
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.type.startsWith('image/')) {
            // Check file size (16MB limit)
            if (file.size > 16 * 1024 * 1024) {
                showToast('Image file is too large. Please select an image under 16MB.', 'error');
                return;
            }
            selectedFile = file;
            displayImagePreview(file);
            document.getElementById('imageSearchBtn').disabled = false;
        } else {
            showToast('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
        }
    }
}

function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
    
    const file = event.dataTransfer.files[0];
    if (file) {
        if (file.type.startsWith('image/')) {
            // Check file size (16MB limit)
            if (file.size > 16 * 1024 * 1024) {
                showToast('Image file is too large. Please select an image under 16MB.', 'error');
                return;
            }
            selectedFile = file;
            displayImagePreview(file);
            document.getElementById('imageSearchBtn').disabled = false;
        } else {
            showToast('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
        }
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.currentTarget.classList.remove('drag-over');
}

function displayImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('previewImg').src = e.target.result;
        
        // Display file information
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const fileInfo = `${file.name} (${fileSizeMB} MB, ${file.type})`;
        document.getElementById('imageInfo').textContent = fileInfo;
        
        document.getElementById('imagePreview').classList.remove('d-none');
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    selectedFile = null;
    document.getElementById('imageFile').value = '';
    document.getElementById('imagePreview').classList.add('d-none');
    document.getElementById('imageSearchBtn').disabled = true;
}

// Combined search file handling
function handleCombinedFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.type.startsWith('image/')) {
            // Check file size (16MB limit)
            if (file.size > 16 * 1024 * 1024) {
                showToast('Image file is too large. Please select an image under 16MB.', 'error');
                return;
            }
            selectedCombinedFile = file;
            displayCombinedImagePreview(file);
        } else {
            showToast('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
        }
    }
}

function handleCombinedDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
    
    const file = event.dataTransfer.files[0];
    if (file) {
        if (file.type.startsWith('image/')) {
            // Check file size (16MB limit)
            if (file.size > 16 * 1024 * 1024) {
                showToast('Image file is too large. Please select an image under 16MB.', 'error');
                return;
            }
            selectedCombinedFile = file;
            displayCombinedImagePreview(file);
        } else {
            showToast('Please select a valid image file (JPG, PNG, GIF, WEBP)', 'error');
        }
    }
}

function displayCombinedImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('combinedPreviewImg').src = e.target.result;
        
        // Display file information
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const fileInfo = `${file.name} (${fileSizeMB} MB, ${file.type})`;
        document.getElementById('combinedImageInfo').textContent = fileInfo;
        
        document.getElementById('combinedImagePreview').classList.remove('d-none');
    };
    reader.readAsDataURL(file);
}

function clearCombinedImage() {
    selectedCombinedFile = null;
    document.getElementById('combinedImageFile').value = '';
    document.getElementById('combinedImagePreview').classList.add('d-none');
}

// Display results
function displayResults(results) {
    const resultsContainer = document.getElementById('resultsContainer');
    const searchResults = document.getElementById('searchResults');
    const noResults = document.getElementById('noResults');
    const resultCount = document.getElementById('resultCount');
    
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        searchResults.classList.add('d-none');
        noResults.classList.remove('d-none');
        return;
    }
    
    noResults.classList.add('d-none');
    searchResults.classList.remove('d-none');
    resultCount.textContent = results.length;
    
    results.forEach(product => {
        const card = createProductCard(product);
        resultsContainer.appendChild(card);
    });
}

function createProductCard(product) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4 mb-4';
    
    const imageUrl = product.images && product.images.length > 0 
        ? product.images[0].url 
        : '/static/images/placeholder.svg';
    
    // Determine badge color and icon based on search source
    let badgeClass = 'similarity-badge-default';
    let badgeIcon = '';
    let badgeTitle = 'Match';
    
    if (product.search_source) {
        switch (product.search_source) {
            case 'vector':
            case 'vector_image':
            case 'vector_text_image':
            case 'text_primary':
            case 'image_secondary':
                badgeClass = 'similarity-badge-vector';
                badgeIcon = '<i class="bi bi-cpu me-1"></i>';
                badgeTitle = 'AI Match';
                break;
            case 'database':
            case 'database_fallback':
            case 'fallback':
            case 'text_fallback':
            case 'image_fallback':
                badgeClass = 'similarity-badge-keyword';
                badgeIcon = '<i class="bi bi-search me-1"></i>';
                badgeTitle = 'Keyword Match';
                break;
            default:
                badgeClass = 'similarity-badge-default';
                badgeIcon = '<i class="bi bi-question-circle me-1"></i>';
                badgeTitle = 'Match';
        }
    }
    
    const similarityScore = product.similarity_score 
        ? `<span class="similarity-badge ${badgeClass}" title="${badgeTitle} from ${product.search_source || 'unknown'} search">
             ${badgeIcon}${Math.round(product.similarity_score * 100)}%
           </span>` 
        : '';
    
    col.innerHTML = `
        <div class="card product-card h-100" onclick="showProductDetail(${product.id})">
            <div class="position-relative">
                <img src="${imageUrl}" class="card-img-top product-image" alt="${product.title}">
                ${similarityScore}
            </div>
            <div class="card-body">
                <h5 class="card-title">${product.title}</h5>
                <p class="card-text text-muted small">${product.vendor || ''}</p>
                <p class="card-text">${product.description ? product.description.substring(0, 100) + '...' : ''}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="h5 mb-0 text-primary">${formatCurrency(product.price || 0)}</span>
                    <small class="text-muted">SKU: ${product.sku_code || 'N/A'}</small>
                </div>
            </div>
        </div>
    `;
    
    return col;
}

async function showProductDetail(productId) {
    try {
        const product = await apiCall(`/skus/${productId}`);
        
        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        document.getElementById('productModalTitle').textContent = product.title;
        
        const modalBody = document.getElementById('productModalBody');
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    ${product.images && product.images.length > 0 ? `
                        <div id="productCarousel" class="carousel slide" data-bs-ride="carousel">
                            <div class="carousel-inner">
                                ${product.images.map((img, idx) => `
                                    <div class="carousel-item ${idx === 0 ? 'active' : ''}">
                                        <img src="${img.url}" class="d-block w-100" alt="${img.alt_text || ''}">
                                    </div>
                                `).join('')}
                            </div>
                            ${product.images.length > 1 ? `
                                <button class="carousel-control-prev" type="button" data-bs-target="#productCarousel" data-bs-slide="prev">
                                    <span class="carousel-control-prev-icon"></span>
                                </button>
                                <button class="carousel-control-next" type="button" data-bs-target="#productCarousel" data-bs-slide="next">
                                    <span class="carousel-control-next-icon"></span>
                                </button>
                            ` : ''}
                        </div>
                    ` : '<p>No images available</p>'}
                </div>
                <div class="col-md-6">
                    <h4>${product.title}</h4>
                    <p class="text-muted">${product.vendor || ''}</p>
                    <h3 class="text-primary">${formatCurrency(product.price || 0)}</h3>
                    ${product.compare_at_price ? `<p class="text-muted"><s>${formatCurrency(product.compare_at_price)}</s></p>` : ''}
                    
                    <p><strong>SKU:</strong> ${product.sku_code || 'N/A'}</p>
                    <p><strong>Type:</strong> ${product.product_type || 'N/A'}</p>
                    <p><strong>Stock:</strong> ${product.quantity || 0} units</p>
                    
                    ${product.description ? `
                        <hr>
                        <h5>Description</h5>
                        <div>${product.description}</div>
                    ` : ''}
                    
                    ${product.tags && product.tags.length > 0 ? `
                        <hr>
                        <h5>Tags</h5>
                        <div>
                            ${product.tags.map(tag => `<span class="badge bg-secondary me-1">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                    
                    ${product.categories && product.categories.length > 0 ? `
                        <hr>
                        <h5>Categories</h5>
                        <div>
                            ${product.categories.map(cat => `<span class="badge bg-info me-1">${cat.name}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        modal.show();
    } catch (error) {
        showToast('Failed to load product details', 'error');
    }
}

// Loading states
function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('searchResults').classList.add('d-none');
    document.getElementById('noResults').classList.add('d-none');
}

function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('d-none');
}

// Example image functionality
function loadExampleImage(category) {
    // Create a sample search based on category
    const sampleQueries = {
        'shoes': 'shoes sneakers footwear',
        'electronics': 'laptop computer phone tablet',
        'clothing': 'shirt dress jacket pants'
    };
    
    // Switch to text search tab and perform search
    const textTab = document.querySelector('#text-tab');
    const textSearchPane = document.querySelector('#text-search');
    const imageTab = document.querySelector('#image-tab');
    const imageSearchPane = document.querySelector('#image-search');
    
    // Switch tabs
    textTab.classList.add('active');
    textSearchPane.classList.add('show', 'active');
    imageTab.classList.remove('active');
    imageSearchPane.classList.remove('show', 'active');
    
    // Set search query and perform search
    const searchQuery = document.getElementById('searchQuery');
    searchQuery.value = sampleQueries[category] || category;
    
    // Trigger search
    performTextSearch({ preventDefault: () => {} });
    
    showToast(`Searching for ${category} products...`, 'info');
}

// Enhanced error handling for image search
function validateImageFile(file) {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (!allowedTypes.includes(file.type)) {
        return 'Please select a valid image file (JPG, PNG, GIF, WEBP)';
    }
    
    if (file.size > maxSize) {
        return 'Image file is too large. Please select an image under 16MB.';
    }
    
    return null; // No error
}

// Improved image upload feedback
function showImageUploadProgress() {
    const btn = document.getElementById('imageSearchBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing image...';
    
    return () => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    };
}

// Combined search progress feedback
function showCombinedSearchProgress() {
    const btn = document.getElementById('combinedSearchBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing search...';
    
    return () => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    };
}

// Combined search examples
function loadCombinedExample(query, category) {
    // Switch to combined search tab
    const combinedTab = document.querySelector('#combined-tab');
    const combinedSearchPane = document.querySelector('#combined-search');
    const textTab = document.querySelector('#text-tab');
    const textSearchPane = document.querySelector('#text-search');
    const imageTab = document.querySelector('#image-tab');
    const imageSearchPane = document.querySelector('#image-search');
    
    // Switch tabs
    combinedTab.classList.add('active');
    combinedSearchPane.classList.add('show', 'active');
    textTab.classList.remove('active');
    textSearchPane.classList.remove('show', 'active');
    imageTab.classList.remove('active');
    imageSearchPane.classList.remove('show', 'active');
    
    // Set search query
    const combinedSearchQuery = document.getElementById('combinedSearchQuery');
    combinedSearchQuery.value = query;
    
    showToast(`Example loaded: "${query}" + ${category} image. Add an image for better results!`, 'info');
}