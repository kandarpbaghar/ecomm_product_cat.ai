// Cart Management System
class CartManager {
    constructor() {
        this.cart = this.loadCart();
        this.listeners = [];
    }

    // Load cart from localStorage
    loadCart() {
        const savedCart = localStorage.getItem('shopping_cart');
        return savedCart ? JSON.parse(savedCart) : {};
    }

    // Save cart to localStorage
    saveCart() {
        localStorage.setItem('shopping_cart', JSON.stringify(this.cart));
        this.notifyListeners();
    }

    // Add item to cart
    addToCart(productId, productData) {
        if (this.cart[productId]) {
            this.cart[productId].quantity += 1;
        } else {
            this.cart[productId] = {
                ...productData,
                quantity: 1,
                addedAt: new Date().toISOString()
            };
        }
        this.saveCart();
        this.showNotification('Item added to cart');
    }

    // Update quantity
    updateQuantity(productId, quantity) {
        if (quantity <= 0) {
            this.removeFromCart(productId);
        } else if (this.cart[productId]) {
            this.cart[productId].quantity = quantity;
            this.saveCart();
        }
    }

    // Increase quantity
    increaseQuantity(productId) {
        if (this.cart[productId]) {
            this.cart[productId].quantity += 1;
            this.saveCart();
        }
    }

    // Decrease quantity
    decreaseQuantity(productId) {
        if (this.cart[productId]) {
            if (this.cart[productId].quantity > 1) {
                this.cart[productId].quantity -= 1;
                this.saveCart();
            } else {
                this.removeFromCart(productId);
            }
        }
    }

    // Remove item from cart
    removeFromCart(productId) {
        if (this.cart[productId]) {
            delete this.cart[productId];
            this.saveCart();
            this.showNotification('Item removed from cart');
        }
    }

    // Get cart item
    getCartItem(productId) {
        return this.cart[productId] || null;
    }

    // Get total items count
    getTotalItems() {
        return Object.values(this.cart).reduce((total, item) => total + item.quantity, 0);
    }

    // Get cart total price
    getTotalPrice() {
        return Object.values(this.cart).reduce((total, item) => {
            const price = parseFloat(item.price) || 0;
            return total + (price * item.quantity);
        }, 0);
    }

    // Clear cart
    clearCart() {
        this.cart = {};
        this.saveCart();
        this.showNotification('Cart cleared');
    }

    // Add listener for cart changes
    addListener(callback) {
        this.listeners.push(callback);
    }

    // Notify all listeners
    notifyListeners() {
        this.listeners.forEach(callback => callback(this));
    }

    // Show notification
    showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'cart-notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 10);

        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Get all cart items
    getCartItems() {
        return Object.entries(this.cart).map(([id, item]) => ({
            id: parseInt(id),
            ...item
        }));
    }
}

// Initialize cart manager
const cartManager = new CartManager();

// Update cart UI on page load and cart changes
function updateCartUI() {
    updateCartBadge();
    updateProductCards();
}

// Update cart badge
function updateCartBadge() {
    const totalItems = cartManager.getTotalItems();
    const cartBadge = document.getElementById('cart-badge');
    const cartCount = document.getElementById('cart-count');
    
    if (cartBadge && cartCount) {
        cartCount.textContent = totalItems;
        cartBadge.style.display = totalItems > 0 ? 'flex' : 'none';
    }
}

// Update product cards to show quantity controls
function updateProductCards() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const productId = parseInt(card.dataset.productId);
        const cartItem = cartManager.getCartItem(productId);
        const actionsDiv = card.querySelector('.product-actions');
        
        if (cartItem && actionsDiv) {
            // Replace add to cart button with quantity controls
            actionsDiv.innerHTML = `
                <div class="cart-controls">
                    <button class="quantity-btn minus" onclick="event.stopPropagation(); decreaseQuantity(${productId})">
                        <i class="fas fa-minus"></i>
                    </button>
                    <span class="quantity-display">${cartItem.quantity}</span>
                    <button class="quantity-btn plus" onclick="event.stopPropagation(); increaseQuantity(${productId})">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="remove-btn" onclick="event.stopPropagation(); removeFromCart(${productId})" title="Remove from cart">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <button class="quick-view-btn" onclick="event.stopPropagation(); quickView(${productId})">
                    <i class="fas fa-eye"></i>
                </button>
            `;
        } else if (actionsDiv && !actionsDiv.querySelector('.add-to-cart-btn')) {
            // Restore add to cart button if item was removed
            actionsDiv.innerHTML = `
                <button class="add-to-cart-btn" onclick="event.stopPropagation(); addToCart(${productId})">
                    <i class="fas fa-shopping-cart"></i> <span class="btn-text">Add to Cart</span>
                </button>
                <button class="quick-view-btn" onclick="event.stopPropagation(); quickView(${productId})">
                    <i class="fas fa-eye"></i>
                </button>
            `;
        }
    });
}

// Global functions for onclick handlers
function addToCart(productId) {
    const productCard = document.querySelector(`[data-product-id="${productId}"]`);
    if (productCard) {
        const titleElement = productCard.querySelector('.product-title, h3, h4');
        const priceElement = productCard.querySelector('.current-price');
        const vendorElement = productCard.querySelector('.product-vendor');
        const imageElement = productCard.querySelector('.product-image, img');
        
        if (titleElement && priceElement) {
            const productData = {
                id: productId,
                title: titleElement.textContent.trim(),
                price: priceElement.textContent.replace('$', '').trim(),
                vendor: vendorElement ? vendorElement.textContent.trim() : 'Unknown',
                image: imageElement ? imageElement.src : '/static/images/placeholder.svg'
            };
            cartManager.addToCart(productId, productData);
            updateCartUI();
        } else {
            console.error('Could not find product details for product:', productId);
        }
    } else {
        console.error('Product card not found for product:', productId);
    }
}

function increaseQuantity(productId) {
    cartManager.increaseQuantity(productId);
    updateCartUI();
    // Re-render cart dropdown if it's open
    const cartDropdown = document.getElementById('cart-dropdown');
    if (cartDropdown && cartDropdown.classList.contains('show')) {
        renderCartItems();
    }
}

function decreaseQuantity(productId) {
    cartManager.decreaseQuantity(productId);
    updateCartUI();
    // Re-render cart dropdown if it's open
    const cartDropdown = document.getElementById('cart-dropdown');
    if (cartDropdown && cartDropdown.classList.contains('show')) {
        renderCartItems();
    }
}

function removeFromCart(productId) {
    cartManager.removeFromCart(productId);
    updateCartUI();
    // Re-render cart dropdown if it's open
    const cartDropdown = document.getElementById('cart-dropdown');
    if (cartDropdown && cartDropdown.classList.contains('show')) {
        renderCartItems();
    }
}

// Toggle cart dropdown
function toggleCart() {
    const cartDropdown = document.getElementById('cart-dropdown');
    if (cartDropdown) {
        cartDropdown.classList.toggle('show');
        if (cartDropdown.classList.contains('show')) {
            renderCartItems();
        }
    }
}

// Render cart items in dropdown
function renderCartItems() {
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const emptyCart = document.getElementById('empty-cart');
    
    if (!cartItemsContainer) return;
    
    const items = cartManager.getCartItems();
    
    if (items.length === 0) {
        cartItemsContainer.style.display = 'none';
        if (emptyCart) emptyCart.style.display = 'block';
        if (cartTotal) cartTotal.style.display = 'none';
    } else {
        cartItemsContainer.style.display = 'block';
        if (emptyCart) emptyCart.style.display = 'none';
        if (cartTotal) cartTotal.style.display = 'block';
        
        cartItemsContainer.innerHTML = items.map(item => `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.title}" class="cart-item-image">
                <div class="cart-item-details">
                    <div class="cart-item-title">${item.title}</div>
                    <div class="cart-item-price">$${item.price}</div>
                </div>
                <div class="cart-item-controls">
                    <button class="quantity-btn minus" onclick="decreaseQuantity(${item.id})">
                        <i class="fas fa-minus"></i>
                    </button>
                    <span class="quantity-display">${item.quantity}</span>
                    <button class="quantity-btn plus" onclick="increaseQuantity(${item.id})">
                        <i class="fas fa-plus"></i>
                    </button>
                    <button class="cart-item-delete" onclick="removeFromCart(${item.id})" title="Remove from cart">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        if (cartTotal) {
            const totalPrice = cartManager.getTotalPrice();
            cartTotal.innerHTML = `
                <div class="cart-total-label">Total:</div>
                <div class="cart-total-amount">$${totalPrice.toFixed(2)}</div>
            `;
        }
    }
}

// Close cart dropdown when clicking outside
document.addEventListener('click', (e) => {
    const cartContainer = document.querySelector('.cart-container');
    const cartDropdown = document.getElementById('cart-dropdown');
    
    // Don't close if clicking on cart controls
    if (e.target.closest('.cart-controls') || 
        e.target.closest('.cart-item-controls') || 
        e.target.closest('.quantity-btn') || 
        e.target.closest('.cart-item-delete')) {
        return;
    }
    
    if (cartDropdown && cartContainer && !cartContainer.contains(e.target)) {
        cartDropdown.classList.remove('show');
    }
});

// Listen for cart changes
cartManager.addListener(() => {
    updateCartUI();
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
});