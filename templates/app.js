// app.js - Mock Database & Shared Logic

// --- Mock Data ---
const DB = {
    users: [
        { id: 1, name: 'Admin System', email: 'admin@demo.com', role: 'admin', avatar: 'A' },
        { id: 2, name: 'John Seller', email: 'seller@demo.com', role: 'seller', avatar: 'S', shopName: 'Tech Haven' },
        { id: 3, name: 'Mary Customer', email: 'customer@demo.com', role: 'customer', avatar: 'C' }
    ],
    sellers: [ // Seller details
        { id: 2, userId: 2, shopName: 'Tech Haven', status: 'approved', joinedAt: '2023-01-15', totalProducts: 45, totalSales: 15000 }
    ],
    sellerRequests: [
        { id: 101, shopName: 'Fashion Hub', ownerName: 'Alice', email: 'alice@shop.com', status: 'pending', date: '2023-11-20' },
        { id: 102, shopName: 'Gadget Pro', ownerName: 'Bob', email: 'bob@gadget.com', status: 'rejected', date: '2023-11-18' }
    ],
    products: [
        { id: 1, sellerId: 2, name: 'Wireless Headphones', price: 99.99, stock: 50, category: 'Electronics', status: 'active', image: 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=300&q=80' },
        { id: 2, sellerId: 2, name: 'Smart Watch', price: 199.99, stock: 30, category: 'Electronics', status: 'active', image: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=300&q=80' },
        { id: 3, sellerId: 2, name: 'Mechanical Keyboard', price: 129.99, stock: 0, category: 'Accessories', status: 'out_of_stock', image: 'https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=300&q=80' }
    ],
    orders: [
        { id: 1001, customerId: 3, totalAmount: 299.98, paymentStatus: 'paid', shippingStatus: 'delivered', createdAt: '2023-11-10' },
        { id: 1002, customerId: 3, totalAmount: 99.99, paymentStatus: 'pending', shippingStatus: 'pending', createdAt: '2023-11-22' }
    ],
    orderItems: [
        { id: 1, orderId: 1001, productId: 1, name: 'Wireless Headphones', quantity: 1, price: 99.99 },
        { id: 2, orderId: 1001, productId: 2, name: 'Smart Watch', quantity: 1, price: 199.99 },
        { id: 3, orderId: 1002, productId: 1, name: 'Wireless Headphones', quantity: 1, price: 99.99 }
    ]
};

// --- Session Management ---

function loginAs(role) {
    const user = DB.users.find(u => u.role === role);
    if(user) {
        localStorage.setItem('currentUser', JSON.stringify(user));
        window.location.href = 'dashboard.html';
    }
}

function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

function getCurrentUser() {
    const userStr = localStorage.getItem('currentUser');
    return userStr ? JSON.parse(userStr) : null;
}

// --- Auth & Role Checking ---

function requireAuth(allowedRoles = []) {
    const user = getCurrentUser();
    
    if (!user) {
        window.location.href = 'index.html';
        return null;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
        renderAccessDenied();
        return null;
    }

    return user;
}

function renderAccessDenied() {
    const layout = document.querySelector('.app-layout');
    if(layout) {
        layout.innerHTML = `
            <div class="access-denied" style="width: 100%; height: 100vh; background: var(--bg); display: flex; align-items:center; justify-content:center; flex-direction:column;">
                <i class='bx bx-error-circle' style="font-size: 80px; color: var(--danger); margin-bottom: 20px;"></i>
                <h2 style="font-size: 24px; margin-bottom: 10px;">Access Denied</h2>
                <p style="color: var(--text-light); margin-bottom: 20px;">You don't have permission to view this page.</p>
                <a href="dashboard.html" class="btn btn-primary">Back to Dashboard</a>
            </div>
        `;
    }
}

// --- UI Rendering Builders ---

function renderHeader(user) {
    const headerHtml = `
        <div class="header-search">
            <i class='bx bx-search'></i>
            <input type="text" placeholder="Search...">
        </div>
        <div class="user-profile" onclick="toggleUserDropdown()">
            <div class="user-info text-right">
                <span class="user-name">${user.name}</span>
                <span class="user-role">${user.role}</span>
            </div>
            <div class="avatar">${user.avatar}</div>
        </div>
    `;
    const headerEl = document.getElementById('topHeader');
    if(headerEl) headerEl.innerHTML = headerHtml;
}

function renderSidebarMenu(role, currentPage) {
    const menuEl = document.getElementById('sidebarMenu');
    if (!menuEl) return;

    let html = '';

    // Common
    html += `
        <a href="dashboard.html" class="menu-item ${currentPage === 'dashboard' ? 'active' : ''}">
            <i class='bx bxs-dashboard'></i> Dashboard
        </a>
    `;

    // Admin Menu
    if (role === 'admin') {
        html += `
            <div class="menu-label">Admin Management</div>
            <a href="admin.html" class="menu-item ${currentPage === 'admin' ? 'active' : ''}">
                <i class='bx bx-store-alt'></i> Sellers & Shops
            </a>
        `;
    }

    // Seller Menu
    if (role === 'seller') {
        html += `
            <div class="menu-label">Shop Management</div>
            <a href="seller.html" class="menu-item ${currentPage === 'seller' ? 'active' : ''}">
                <i class='bx bx-plus-circle'></i> Post Product
            </a>
            <a href="shop-products.html" class="menu-item ${currentPage === 'shop-products' ? 'active' : ''}">
                <i class='bx bx-package'></i> My Products
            </a>
        `;
    }

    // Customer Menu
    if (role === 'customer') {
        html += `
            <div class="menu-label">Shopping</div>
            <a href="checkout.html" class="menu-item ${currentPage === 'checkout' ? 'active' : ''}">
                <i class='bx bx-cart'></i> Shop & Checkout
            </a>
            <a href="track-order.html" class="menu-item ${currentPage === 'track-order' ? 'active' : ''}">
                <i class='bx bx-receipt'></i> Track Orders
            </a>
        `;
    }

    // Logout
    html += `
        <div class="menu-label">Account</div>
        <a href="#" onclick="logout(); return false;" class="menu-item" style="color: var(--danger);">
            <i class='bx bx-log-out'></i> Logout
        </a>
    `;

    menuEl.innerHTML = html;
}

// Format Currency
function formatMoney(amount) {
    return '$' + amount.toFixed(2);
}

// Utility to format date
function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}
