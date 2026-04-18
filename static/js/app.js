/**
 * BREW & BOND - Cafe Loyalty System
 * Frontend JavaScript
 */

// ═══════════════════ STATE ═══════════════════
const state = {
    customer: null,
    cart: [],
    orders: [],
    drinks: [],
    currentPage: 'home',
    filter: 'all',
    qrCode: null,
};

// ═══════════════════ API CALLS ═══════════════════
const API = {
    async get(url) {
        const res = await fetch(url);
        return res.json();
    },
    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    }
};

// ═══════════════════ INIT ═══════════════════
document.addEventListener('DOMContentLoaded', async () => {
    // Load drinks
    state.drinks = await API.get('/api/drinks');
    renderDrinksGrid();

    // Setup event listeners
    setupEventListeners();

    // Check for saved session
    const savedId = localStorage.getItem('cafe_customer_id');
    if (savedId) {
        try {
            const data = await API.get(`/api/customer/${savedId}`);
            if (data.customer) {
                state.customer = data.customer;
                state.orders = data.orders || [];
                state.qrCode = data.qr_code;
                navigateTo('menu');
            }
        } catch (e) {
            localStorage.removeItem('cafe_customer_id');
        }
    }
});

// ═══════════════════ NAVIGATION ═══════════════════
function navigateTo(page) {
    state.currentPage = page;

    // Hide all pages
    document.querySelectorAll('.page-section').forEach(el => {
        el.classList.remove('active');
    });

    // Show target page
    const target = document.getElementById(`page-${page}`);
    if (target) {
        target.classList.add('active');
        target.style.animation = 'none';
        target.offsetHeight; // trigger reflow
        target.style.animation = 'fadeUp 0.5s ease-out';
    }

    // Update nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.page === page);
    });

    // Show/hide nav tabs
    const navTabs = document.getElementById('nav-tabs');
    navTabs.style.display = state.customer ? 'flex' : 'none';

    // Update page-specific content
    if (page === 'menu') updateMenuPage();
    if (page === 'card') updateCardPage();
    if (page === 'orders') updateOrdersPage();
}

// ═══════════════════ EVENT LISTENERS ═══════════════════
function setupEventListeners() {
    // Nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (state.customer) navigateTo(tab.dataset.page);
        });
    });

    // Brand click
    document.getElementById('brand-link').addEventListener('click', () => {
        navigateTo(state.customer ? 'menu' : 'home');
    });

    // Registration form
    document.getElementById('btn-register').addEventListener('click', handleRegister);

    // Admin toggle
    document.getElementById('btn-admin-toggle').addEventListener('click', () => {
        const panel = document.getElementById('admin-panel');
        panel.classList.toggle('active');
    });

    // Admin search
    document.getElementById('btn-admin-search').addEventListener('click', handleAdminSearch);

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            state.filter = btn.dataset.filter;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderDrinksGrid();
        });
    });

    // Cart bar checkout
    document.getElementById('cart-bar').addEventListener('click', handleCheckout);

    // Card page buttons
    document.getElementById('btn-order-now')?.addEventListener('click', () => navigateTo('menu'));
    document.getElementById('btn-view-orders')?.addEventListener('click', () => navigateTo('orders'));

    // Wallet buttons
    document.getElementById('btn-apple-pay')?.addEventListener('click', handleApplePay);
    document.getElementById('btn-samsung-pay')?.addEventListener('click', handleSamsungPay);

    // Enter key on registration
    document.getElementById('input-name').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleRegister();
    });
    document.getElementById('input-phone').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleRegister();
    });
}

// ═══════════════════ REGISTRATION ═══════════════════
async function handleRegister() {
    const name = document.getElementById('input-name').value.trim();
    const phone = document.getElementById('input-phone').value.trim();

    if (!name) {
        showNotification('الرجاء إدخال الاسم', 'error');
        return;
    }

    try {
        const data = await API.post('/api/register', { name, phone });
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }

        state.customer = data.customer;
        state.qrCode = data.qr_code;
        state.orders = [];
        state.cart = [];

        localStorage.setItem('cafe_customer_id', data.customer.id);
        showNotification(data.message);
        navigateTo('menu');
    } catch (err) {
        showNotification('حدث خطأ، حاول مرة أخرى', 'error');
    }
}

// ═══════════════════ ADMIN SEARCH ═══════════════════
async function handleAdminSearch() {
    const id = document.getElementById('input-lookup').value.trim().toUpperCase();
    if (!id) return;

    try {
        const data = await API.get(`/api/customer/${id}`);
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }

        state.customer = data.customer;
        state.orders = data.orders || [];
        state.qrCode = data.qr_code;
        localStorage.setItem('cafe_customer_id', data.customer.id);
        showNotification('تم العثور على العميل!');
        navigateTo('card');
    } catch (err) {
        showNotification('لم يتم العثور على العميل', 'error');
    }
}

// ═══════════════════ DRINKS MENU ═══════════════════
function renderDrinksGrid() {
    const grid = document.getElementById('drinks-grid');
    if (!grid) return;

    const filtered = state.filter === 'all'
        ? state.drinks
        : state.drinks.filter(d => d.category === state.filter);

    grid.innerHTML = filtered.map(drink => {
        const inCart = state.cart.find(c => c.id === drink.id);
        return `
            <div class="drink-card ${inCart ? 'in-cart' : ''}" onclick="addToCart(${drink.id})">
                ${inCart ? `<div class="qty-badge">${inCart.qty}</div>` : ''}
                <div class="emoji">${drink.emoji}</div>
                <div class="name">${drink.name}</div>
                <div class="name-en">${drink.name_en}</div>
                <div class="price">${drink.price} ر.س</div>
            </div>
        `;
    }).join('');

    updateCartBar();
}

function addToCart(drinkId) {
    const drink = state.drinks.find(d => d.id === drinkId);
    if (!drink) return;

    const existing = state.cart.find(c => c.id === drinkId);
    if (existing) {
        existing.qty += 1;
    } else {
        state.cart.push({ ...drink, qty: 1 });
    }

    renderDrinksGrid();
}

function updateCartBar() {
    const bar = document.getElementById('cart-bar');
    const count = state.cart.reduce((s, i) => s + i.qty, 0);
    const total = state.cart.reduce((s, i) => s + i.price * i.qty, 0);

    if (count > 0) {
        bar.classList.add('visible');
        document.getElementById('cart-count').textContent = `${count} عنصر • ${total} ر.س`;
        document.getElementById('cart-emojis').innerHTML =
            state.cart.map(i => `<span>${i.emoji}</span>`).join('') +
            '<span style="margin-right:4px">←</span>';
    } else {
        bar.classList.remove('visible');
    }
}

function updateMenuPage() {
    if (!state.customer) return;

    const c = state.customer;
    document.getElementById('welcome-name').textContent = `أهلاً ${c.name} 👋`;
    document.getElementById('welcome-stamps').textContent =
        `${c.stamps}/7 نقاط • باقي ${7 - c.stamps} للمجاني`;
    document.getElementById('welcome-id').textContent = c.id;
}

// ═══════════════════ CHECKOUT ═══════════════════
async function handleCheckout() {
    if (state.cart.length === 0) return;

    const items = state.cart.map(i => ({ id: i.id, qty: i.qty }));

    try {
        const data = await API.post('/api/order', {
            customer_id: state.customer.id,
            items: items,
        });

        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }

        state.customer = data.customer;
        state.qrCode = data.qr_code;
        state.orders.unshift(data.order);
        state.cart = [];

        if (data.free_this_order > 0) {
            showConfetti();
        }

        showNotification(data.message);
        navigateTo('card');
    } catch (err) {
        showNotification('حدث خطأ في الطلب', 'error');
    }
}

// ═══════════════════ CARD PAGE ═══════════════════
function updateCardPage() {
    if (!state.customer) return;

    const c = state.customer;
    const stamps = c.stamps;

    // Stamp grid
    const stampGrid = document.getElementById('stamp-grid');
    stampGrid.innerHTML = Array.from({ length: 7 }, (_, i) => `
        <div class="stamp ${i < stamps ? 'filled' : 'empty'}">
            ${i < stamps ? '☕' : (i === 6 ? '🎁' : (i + 1))}
        </div>
    `).join('');

    // Subtitle
    const subtitle = document.getElementById('card-subtitle');
    if (stamps === 0 && c.free_earned === 0) {
        subtitle.textContent = 'ابدأ بجمع النقاط الآن!';
    } else {
        let text = `باقي ${7 - stamps} مشروبات للمجاني`;
        if (c.free_earned > 0) text += ` • حصلت على ${c.free_earned} مشروب مجاني 🎉`;
        subtitle.textContent = text;
    }

    // Progress
    document.getElementById('progress-value').textContent = `${stamps}/7`;
    document.getElementById('progress-fill').style.width = `${(stamps / 7) * 100}%`;

    // Wallet card info
    document.getElementById('wallet-name').textContent = c.name || 'عميل جديد';
    document.getElementById('wallet-id').textContent = c.id;
    document.getElementById('wallet-stamps').textContent = `${stamps} / 7`;

    // Wallet progress
    document.getElementById('wallet-progress-fill').style.width = `${(stamps / 7) * 100}%`;

    // QR Code
    if (state.qrCode) {
        document.getElementById('qr-image').src = `data:image/png;base64,${state.qrCode}`;
    }
}

// ═══════════════════ ORDERS PAGE ═══════════════════
function updateOrdersPage() {
    const container = document.getElementById('orders-list');
    if (!container) return;

    if (state.orders.length === 0) {
        container.innerHTML = `
            <div class="orders-empty">
                <div class="icon">📋</div>
                لا توجد طلبات بعد
            </div>
        `;
        return;
    }

    container.innerHTML = state.orders.map(order => `
        <div class="order-card ${order.free_earned > 0 ? 'has-free' : ''}">
            <div class="order-header">
                <span class="order-id">${order.id}</span>
                <span class="order-date">${order.date}</span>
            </div>
            <div class="order-items">
                ${order.items.map(item => `
                    <span class="order-item-tag">${item.emoji} ${item.name} ×${item.qty}</span>
                `).join('')}
            </div>
            <div class="order-footer">
                <span class="order-total">${order.total} ر.س</span>
                ${order.free_earned > 0
                    ? `<span class="order-free-badge">🎁 +${order.free_earned} مجاني</span>`
                    : ''}
            </div>
        </div>
    `).join('');
}

// ═══════════════════ WALLET ═══════════════════
function handleApplePay() {
    if (!state.customer) return;
    // In production: generate .pkpass file
    window.open(`/api/wallet/${state.customer.id}`, '_blank');
    showNotification('جاري تحميل بطاقة Apple Wallet...');
}

function handleSamsungPay() {
    if (!state.customer) return;
    // In production: integrate with Samsung Wallet API
    window.open(`/api/wallet/${state.customer.id}`, '_blank');
    showNotification('جاري تحميل بطاقة Samsung Pay...');
}

// ═══════════════════ NOTIFICATIONS ═══════════════════
function showNotification(msg, type = 'success') {
    // Remove existing
    document.querySelectorAll('.notification').forEach(n => n.remove());

    const el = document.createElement('div');
    el.className = `notification ${type}`;
    el.textContent = msg;
    document.body.appendChild(el);

    setTimeout(() => el.remove(), 3000);
}

// ═══════════════════ CONFETTI ═══════════════════
function showConfetti() {
    const container = document.createElement('div');
    container.className = 'confetti-container';

    const colors = ['#c8956c', '#e8b88a', '#a0724e', '#f5d4b3', '#FFD700'];

    for (let i = 0; i < 40; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        const size = 6 + Math.random() * 8;
        piece.style.cssText = `
            left: ${Math.random() * 100}%;
            width: ${size}px;
            height: ${size}px;
            background: ${colors[i % colors.length]};
            border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
            animation-duration: ${1.5 + Math.random()}s;
            animation-delay: ${Math.random() * 0.5}s;
        `;
        container.appendChild(piece);
    }

    document.body.appendChild(container);
    setTimeout(() => container.remove(), 3000);
}
