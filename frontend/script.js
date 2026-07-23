document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const generatorForm = document.getElementById('generator-form');
    const generateBtn = document.getElementById('generate-btn');
    const urlInput = document.getElementById('product-url');
    const resultSection = document.getElementById('result-section');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    const affiliateLinkInput = document.getElementById('affiliate-link');
    const copyBtn = document.getElementById('copy-btn');
    const copyBtnText = document.getElementById('copy-btn-text');
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const checkoutBtn = document.getElementById('checkout-btn');
    const inputSection = document.querySelector('.input-section') || document.getElementById('input-section');
    const resetBtn = document.getElementById('reset-btn');
    
    const previewContainer = document.getElementById('product-preview');
    const previewImage = document.getElementById('preview-image');
    const previewTitle = document.getElementById('preview-title');

    // Toast Container
    const toastContainer = document.getElementById('toast-container');

    // Toast System Helper
    function showToast(message, type = 'info', title = '') {
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type}`;

        const icons = {
            success: '✅',
            error: '⚠️',
            info: '💡',
            warning: '⌛'
        };

        const titles = {
            success: title || 'Success',
            error: title || 'Notice',
            info: title || 'Info',
            warning: title || 'Warning'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || '💡'}</div>
            <div class="toast-content">
                <div class="toast-title">${titles[type]}</div>
                <div class="toast-msg">${message}</div>
            </div>
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 250);
        }, 3500);
    }

    // Global State for Cashback Cart
    let currentGeneratedItem = null;

    function setCurrentItem(url, deeplink, trackingId, previewData = null) {
        currentGeneratedItem = {
            id: trackingId || 'trk_' + Date.now(),
            url: url,
            deeplink: deeplink,
            tracking_id: trackingId || 'trk_' + Date.now(),
            cashback_amount: 5.00,
            title: (previewData && previewData.title) ? previewData.title : url,
            image: (previewData && previewData.image) ? previewData.image : '',
            created_at: new Date().toISOString()
        };
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatLocalDateTime(dateStr) {
        if (!dateStr) return '---';
        let s = String(dateStr);
        if (!s.endsWith('Z') && !s.includes('+') && !s.includes('-', 11)) {
            s = s.replace(' ', 'T') + 'Z';
        }
        const d = new Date(s);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function parseUTCDate(dateStr) {
        if (!dateStr) return new Date();
        let s = String(dateStr).trim();
        if (!s.endsWith('Z') && !s.includes('+') && !s.includes('-', 11)) {
            s = s.replace(' ', 'T') + 'Z';
        }
        let d = new Date(s);
        if (isNaN(d.getTime())) {
            d = new Date(String(dateStr).replace(' ', 'T'));
        }
        if (isNaN(d.getTime())) {
            d = new Date();
        }
        return d;
    }

    function getCountdownTimerHTML(createdAtStr, status) {
        const st = (status || '').toLowerCase();
        if (st === 'approved' || st === 'validated' || st === 'paid') {
            return `<span class="badge approved" style="font-weight: 600;">✅ Validated</span>`;
        }

        const createdDate = parseUTCDate(createdAtStr);
        const expiresAt = createdDate.getTime() + (24 * 60 * 60 * 1000);
        const now = Date.now();
        const diffMs = expiresAt - now;

        if (diffMs <= 0) {
            return `<span class="badge" style="background: rgba(239,68,68,0.15); color: #ef4444; font-weight: 700;">🔴 Expired (Deleting...)</span>`;
        }

        const hrs = Math.floor(diffMs / 3600000);
        const mins = Math.floor((diffMs % 3600000) / 60000);
        const secs = Math.floor((diffMs % 60000) / 1000);
        const pad = n => String(n).padStart(2, '0');

        return `<span class="badge pending countdown-timer-pill" data-created="${createdAtStr || createdDate.toISOString()}" style="font-family: var(--font-mono, monospace); font-weight: 600; background: rgba(245, 158, 11, 0.12); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3);">⏳ ${pad(hrs)}:${pad(mins)}:${pad(secs)} left</span>`;
    }

    // Live Interval: Updates all live countdown timers on screen every second
    setInterval(() => {
        const timerElements = document.querySelectorAll('.countdown-timer-pill');
        const now = Date.now();

        timerElements.forEach(el => {
            const createdStr = el.getAttribute('data-created');
            if (!createdStr) return;

            let s = String(createdStr);
            if (!s.endsWith('Z') && !s.includes('+') && !s.includes('-', 11)) {
                s = s.replace(' ', 'T') + 'Z';
            }
            const createdDate = new Date(s);
            if (isNaN(createdDate.getTime())) return;

            const expiresAt = createdDate.getTime() + (24 * 60 * 60 * 1000);
            const diffMs = expiresAt - now;

            if (diffMs <= 0) {
                el.className = 'badge';
                el.style.background = 'rgba(239,68,68,0.15)';
                el.style.color = '#ef4444';
                el.style.fontWeight = '700';
                el.textContent = '🔴 Expired (Deleting...)';
            } else {
                const hrs = Math.floor(diffMs / 3600000);
                const mins = Math.floor((diffMs % 3600000) / 60000);
                const secs = Math.floor((diffMs % 60000) / 1000);
                const pad = n => String(n).padStart(2, '0');
                el.textContent = `⏳ ${pad(hrs)}:${pad(mins)}:${pad(secs)} left`;
            }
        });
    }, 1000);

    function cleanProductTitle(rawTitle, rawUrl) {
        if (rawTitle && typeof rawTitle === 'string' && !rawTitle.startsWith('http://') && !rawTitle.startsWith('https://')) {
            let t = rawTitle.trim().replace(/-i\.\d+\.\d+/g, '').replace(/[-_]/g, ' ');
            if (t.length > 35) return t.substring(0, 35) + '...';
            return t;
        }

        if (!rawUrl) return 'Affiliate Product Item';

        try {
            const cached = localStorage.getItem('preview_' + rawUrl);
            if (cached) {
                const parsed = JSON.parse(cached);
                if (parsed && parsed.title && typeof parsed.title === 'string' && !parsed.title.startsWith('http')) {
                    let t = parsed.title.trim().replace(/-i\.\d+\.\d+/g, '').replace(/[-_]/g, ' ');
                    if (t.length > 35) return t.substring(0, 35) + '...';
                    return t;
                }
            }
        } catch (e) {}

        try {
            const urlObj = new URL(rawUrl);
            const segments = urlObj.pathname.split('/').filter(Boolean);
            
            for (let seg of segments) {
                let cleaned = seg.replace(/-i\.\d+\.\d+/g, '');
                const words = cleaned.split(/[-_]/).filter(w => w.length > 1 && !/^\d+$/.test(w));
                if (words.length > 0) {
                    const firstWord = words[0].toLowerCase();
                    if (!['opaanlp', 'product', 'products', 'item', 'items', 'p', 'universal'].includes(firstWord)) {
                        let titleStr = words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                        if (titleStr.length > 35) return titleStr.substring(0, 35) + '...';
                        return titleStr;
                    }
                }
            }

            if (urlObj.hostname.includes('shopee')) return 'Shopee Verified Product';
            if (urlObj.hostname.includes('lazada')) return 'Lazada Verified Product';
            if (urlObj.hostname.includes('tiktok')) return 'TikTok Shop Product';
        } catch (e) {}

        return 'Affiliate Cashback Product';
    }

    const openLoginBtn = document.getElementById('open-login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const userNameSpan = document.getElementById('user-name');
    const walletSummaryHeader = document.getElementById('wallet-summary-header');
    const hdrBalance = document.getElementById('hdr-balance');
    const hdrPending = document.getElementById('hdr-pending');

    const wBalance = document.getElementById('w-balance');
    const wPending = document.getElementById('w-pending');
    const wPaid = document.getElementById('w-paid');

    const adminTabBtn = document.getElementById('admin-tab-btn');

    // Modals
    const loginModal = document.getElementById('login-modal');
    const closeLoginBtn = document.getElementById('close-login-btn');
    const quickDemoUser = document.getElementById('quick-demo-user');
    const quickDemoAdmin = document.getElementById('quick-demo-admin');
    const loginForm = document.getElementById('login-form');

    const withdrawModal = document.getElementById('withdraw-modal');
    const openWithdrawBtn = document.getElementById('open-withdraw-btn');
    const closeWithdrawBtn = document.getElementById('close-withdraw-btn');
    const withdrawForm = document.getElementById('withdraw-form');

    const testConvModal = document.getElementById('test-conv-modal');
    const openTestConvBtn = document.getElementById('open-test-conv-btn');
    const closeTestConvBtn = document.getElementById('close-test-conv-btn');
    const testConvForm = document.getElementById('test-conv-form');

    // API URLs dynamically derived from host
    const BASE_URL = window.location.origin;

    let currentUser = null;

    // --- Check URL Parameter for Admin Mode (?admin=true) ---
    const urlParams = new URLSearchParams(window.location.search);
    const isAdminUrlParam = urlParams.get('admin') === 'true' || urlParams.get('admin') === '1';

    // --- Tab Navigation ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    function switchTab(tabId) {
        tabButtons.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        const targetTab = document.getElementById(tabId);
        
        if (targetBtn && targetTab) {
            targetBtn.classList.add('active');
            targetTab.classList.add('active');
        }

        if (tabId === 'tab-cashback') loadCashbackHistory();
        if (tabId === 'tab-wallet') loadWalletData();
        if (tabId === 'tab-admin') loadAdminData();
    }

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // --- Authentication ---
    function getToken() {
        return localStorage.getItem('access_token');
    }

    function getAuthHeaders() {
        const token = getToken();
        return token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
    }

    async function checkAuth() {
        if (isAdminUrlParam) {
            await loginUser('admin@example.com', 'Admin123!', true);
            switchTab('tab-admin');
            return;
        }

        const token = getToken();
        if (!token) {
            await loginUser('john@example.com', 'Password123', false);
            return;
        }

        try {
            const res = await fetch(`${BASE_URL}/api/auth/me`, { headers: getAuthHeaders() });
            if (res.ok) {
                currentUser = await res.json();
                updateUserUI();
                loadWalletData();
            } else {
                localStorage.removeItem('access_token');
                await loginUser('john@example.com', 'Password123', false);
            }
        } catch (e) {
            console.error('Auth check error:', e);
        }
    }

    async function loginUser(email, password, isAutoAdmin = false) {
        try {
            const res = await fetch(`${BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (res.ok) {
                const data = await res.json();
                localStorage.setItem('access_token', data.access_token);
                if (loginModal) loginModal.classList.add('hidden');
                
                const meRes = await fetch(`${BASE_URL}/api/auth/me`, { headers: { 'Authorization': `Bearer ${data.access_token}` } });
                if (meRes.ok) {
                    currentUser = await meRes.json();
                    updateUserUI();
                    loadWalletData();
                    if (isAutoAdmin || currentUser.role === 'admin') {
                        loadAdminData();
                    }
                    if (!isAutoAdmin) {
                        showToast(`Logged in as ${currentUser.name}`, 'success');
                    }
                }
            }
        } catch (e) {
            console.error('Login error:', e);
        }
    }

    function updateUserUI() {
        const isAdmin = isAdminUrlParam || (currentUser && currentUser.role === 'admin');

        if (adminTabBtn) {
            adminTabBtn.style.display = 'inline-block';
        }

        if (currentUser) {
            userNameSpan.textContent = currentUser.name + (isAdmin ? ' (Admin)' : '');
            openLoginBtn.classList.add('hidden');
            logoutBtn.classList.remove('hidden');
            walletSummaryHeader.classList.remove('hidden');
        } else {
            userNameSpan.textContent = 'John Cashback';
            openLoginBtn.classList.add('hidden');
            logoutBtn.classList.remove('hidden');
            walletSummaryHeader.classList.remove('hidden');
        }
    }

    // Modal Controls
    if (openLoginBtn) openLoginBtn.addEventListener('click', () => loginModal.classList.remove('hidden'));
    if (closeLoginBtn) closeLoginBtn.addEventListener('click', () => loginModal.classList.add('hidden'));

    if (quickDemoUser) quickDemoUser.addEventListener('click', () => loginUser('john@example.com', 'Password123'));
    if (quickDemoAdmin) quickDemoAdmin.addEventListener('click', () => loginUser('admin@example.com', 'Admin123!'));

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            loginUser(document.getElementById('login-email').value, document.getElementById('login-password').value);
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            loginUser('john@example.com', 'Password123');
            showToast('Logged out cleanly', 'info');
        });
    }

    // --- Wallet Data ---
    async function loadWalletData() {
        try {
            const res = await fetch(`${BASE_URL}/api/wallet`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                const balance = parseFloat(data.available_balance || 0).toFixed(2);
                const pending = parseFloat(data.pending_cashback || 0).toFixed(2);
                const paid = parseFloat(data.total_paid || 0).toFixed(2);
                const estimated = parseFloat(data.estimated_cashback || 0).toFixed(2);

                if (hdrBalance) hdrBalance.textContent = balance;
                if (hdrPending) hdrPending.textContent = pending;
                
                const hdrEst = document.getElementById('hdr-estimated');
                const hdrPaid = document.getElementById('hdr-paid');
                if (hdrEst) hdrEst.textContent = estimated;
                if (hdrPaid) hdrPaid.textContent = paid;

                if (wBalance) wBalance.textContent = balance;
                if (wPending) wPending.textContent = pending;
                if (wPaid) wPaid.textContent = paid;

                // Cashout Progress Bar towards PHP 100.00
                const balVal = parseFloat(balance);
                const pct = Math.min(100, Math.round((balVal / 100.0) * 100));
                const pctEl = document.getElementById('cashout-progress-pct');
                const barEl = document.getElementById('cashout-progress-bar');
                if (pctEl) pctEl.textContent = `${pct}%`;
                if (barEl) barEl.style.width = `${pct}%`;
            }

            loadMyGeneratedLinks();
            loadPendingCashback();
            loadApprovedCashback();
            loadCashbackHistory();

            const histRes = await fetch(`${BASE_URL}/api/wallet/history`, { headers: getAuthHeaders() });
            if (histRes.ok) {
                const histData = await histRes.json();
                renderWalletHistory(histData.items || []);
            }
        } catch (e) {
            console.error('Wallet fetch error:', e);
        }
    }

    let allMyLinks = [];
    let myLinksCurrentPage = 1;
    let myLinksTotalPages = 1;

    async function loadMyGeneratedLinks(page = 1) {
        myLinksCurrentPage = page;
        const body = document.getElementById('my-links-body');
        if (!body) return;

        try {
            const res = await fetch(`${BASE_URL}/api/affiliate/my-links?page=${myLinksCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                allMyLinks = data.items || [];
                myLinksTotalPages = data.total_pages || 1;

                const elCurrPage = document.getElementById('my-links-curr-page');
                const elTotalPages = document.getElementById('my-links-total-pages');
                const elTotalItems = document.getElementById('my-links-total-items');
                const prevBtn = document.getElementById('my-links-prev-btn');
                const nextBtn = document.getElementById('my-links-next-btn');

                if (elCurrPage) elCurrPage.textContent = myLinksCurrentPage;
                if (elTotalPages) elTotalPages.textContent = myLinksTotalPages;
                if (elTotalItems) elTotalItems.textContent = data.total || allMyLinks.length;

                if (prevBtn) prevBtn.disabled = (myLinksCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (myLinksCurrentPage >= myLinksTotalPages);

                renderMyLinksTable(allMyLinks);
            }
        } catch (e) {
            console.error("My links fetch error:", e);
        }
    }

    const prevLinksBtn = document.getElementById('my-links-prev-btn');
    const nextLinksBtn = document.getElementById('my-links-next-btn');
    if (prevLinksBtn) {
        prevLinksBtn.addEventListener('click', () => {
            if (myLinksCurrentPage > 1) {
                loadMyGeneratedLinks(myLinksCurrentPage - 1);
            }
        });
    }
    if (nextLinksBtn) {
        nextLinksBtn.addEventListener('click', () => {
            if (myLinksCurrentPage < myLinksTotalPages) {
                loadMyGeneratedLinks(myLinksCurrentPage + 1);
            }
        });
    }

    function renderMyLinksTable(links) {
        const body = document.getElementById('my-links-body');
        if (!body) return;

        if (links.length === 0) {
            body.innerHTML = '<tr><td colspan="7" class="empty-msg">No affiliate links generated yet.</td></tr>';
            return;
        }

        let todaySum = 0;
        let lifetimeSum = 0;
        const todayStr = new Date().toDateString();

        body.innerHTML = links.map(l => {
            const statusClass = (l.status || 'generated').toLowerCase();
            const numCashback = parseFloat(l.cashback_amount || 0);
            const val = numCashback > 0 ? numCashback : 5.00;
            const displayCashback = val.toFixed(2);
            const displayTitle = cleanProductTitle(l.product_name || l.title, l.original_url);

            lifetimeSum += val;
            if (new Date(l.created_at).toDateString() === todayStr) {
                todaySum += val;
            }

            const safeTitle = escapeHtml(displayTitle);
            const safeUrl = escapeHtml(l.original_url);
            const safeDeeplink = escapeHtml(l.deeplink);
            const safeTracking = escapeHtml(l.tracking_id);
            const timerHtml = getCountdownTimerHTML(l.created_at, statusClass);

            return `
                <tr>
                    <td>${formatLocalDateTime(l.created_at)}</td>
                    <td><code style="color: var(--color-primary); font-size: 0.82rem; word-break: break-all;">${safeTracking}</code></td>
                    <td style="max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${safeUrl}">
                        <a href="${safeDeeplink}" target="_blank" style="color: var(--color-primary); text-decoration: none; font-weight: 600;">🛍️ ${safeTitle}</a>
                    </td>
                    <td><strong class="tabular-nums" style="color: var(--color-success-text);">₱${displayCashback}</strong></td>
                    <td><span class="badge ${statusClass}">${escapeHtml(l.status || 'Generated')}</span></td>
                    <td>${timerHtml}</td>
                    <td>
                        <button class="nav-btn alt-btn track-timeline-btn" data-tracking="${safeTracking}" data-status="${statusClass}" data-url="${safeUrl}" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;">
                            Timeline ⏱️
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        const elToday = document.getElementById('user-est-today');
        const elLifetime = document.getElementById('user-est-lifetime');
        const elPending = document.getElementById('user-pending-total');
        const hdrPendingEl = document.getElementById('hdr-pending');

        if (elToday) elToday.textContent = `₱${todaySum.toFixed(2)}`;
        if (elLifetime) elLifetime.textContent = `₱${lifetimeSum.toFixed(2)}`;
        if (elPending && hdrPendingEl) elPending.textContent = `₱${hdrPendingEl.textContent}`;

        document.querySelectorAll('.track-timeline-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                openTimelineModal(btn.dataset.tracking, btn.dataset.status, btn.dataset.url);
            });
        });
    }

    // Client-side real-time Search Filter for My Links
    const myLinksSearchInput = document.getElementById('my-links-search');
    if (myLinksSearchInput) {
        myLinksSearchInput.addEventListener('input', () => {
            const query = myLinksSearchInput.value.toLowerCase().trim();
            const filtered = allMyLinks.filter(l => 
                (l.original_url && l.original_url.toLowerCase().includes(query)) ||
                (l.tracking_id && l.tracking_id.toLowerCase().includes(query)) ||
                (l.status && l.status.toLowerCase().includes(query))
            );
            renderMyLinksTable(filtered);
        });
    }

    const timelineModal = document.getElementById('timeline-modal');
    const closeTimelineBtn = document.getElementById('close-timeline-btn');
    if (closeTimelineBtn) closeTimelineBtn.addEventListener('click', () => timelineModal.classList.add('hidden'));

    function openTimelineModal(trackingId, status, url) {
        if (!timelineModal) return;
        
        const trackingCode = document.getElementById('modal-tracking-id');
        const statusText = document.getElementById('modal-status-text');
        const expText = document.getElementById('modal-explanation-text');
        
        if (trackingCode) trackingCode.textContent = trackingId;

        let stage = 1;
        let statusDisplay = "Estimated";
        let statusBadgeClass = "estimated";
        let explanation = "Link generated successfully. When a purchase is completed via this link, your cashback will move to Pending status.";

        const st = (status || 'generated').toLowerCase();
        if (st === 'pending' || st === 'tracked') {
            stage = 3;
            statusDisplay = "Pending Validation";
            statusBadgeClass = "pending";
            explanation = "Your purchase has been tracked by Involve Asia! We are awaiting merchant validation & final order confirmation.";
        } else if (st === 'approved' || st === 'validated' || st === 'available') {
            stage = 4;
            statusDisplay = "Available";
            statusBadgeClass = "approved";
            explanation = "The advertiser has approved the commission! Your cashback is credited to your wallet and available for withdrawal.";
        } else if (st === 'paid') {
            stage = 5;
            statusDisplay = "Paid Out";
            statusBadgeClass = "paid";
            explanation = "Your withdrawal was processed and paid out to your GCash / Bank account.";
        } else if (st === 'rejected' || st === 'cancelled') {
            stage = 2;
            statusDisplay = "Rejected / Cancelled";
            statusBadgeClass = "rejected";
            explanation = "Unfortunately, the advertiser rejected this transaction (e.g. order returned, cancelled, or policy violation).";
        }

        if (statusText) {
            statusText.textContent = statusDisplay;
            statusText.className = `badge ${statusBadgeClass}`;
        }
        if (expText) expText.textContent = explanation;

        for (let i = 1; i <= 5; i++) {
            const node = document.getElementById(`modal-step-node-${i}`);
            const line = document.getElementById(`modal-step-line-${i}`);
            if (node) {
                node.classList.remove('active', 'done');
                if (i < stage) node.classList.add('done');
                if (i === stage) node.classList.add('active');
            }
            if (line) {
                line.classList.remove('active');
                if (i < stage) line.classList.add('active');
            }
        }

        timelineModal.classList.remove('hidden');
    }

    function renderWalletHistory(items) {
        const body = document.getElementById('wallet-history-body');
        if (!body) return;
        if (items.length === 0) {
            body.innerHTML = '<tr><td colspan="4" class="empty-msg">No ledger transactions found.</td></tr>';
            return;
        }

        body.innerHTML = items.map(item => `
            <tr>
                <td>${new Date(item.created_at).toLocaleDateString()}</td>
                <td><span class="badge ${item.type.includes('approved') ? 'approved' : item.type.includes('pending') ? 'pending' : 'rejected'}">${item.type}</span></td>
                <td style="font-weight: 600;" class="tabular-nums">₱${parseFloat(item.amount).toFixed(2)}</td>
                <td>${item.reference || '-'}</td>
            </tr>
        `).join('');
    }

    // --- Cashback History & Status Views ---
    let cashbackHistCurrentPage = 1;
    let cashbackHistTotalPages = 1;

    async function loadCashbackHistory(page = 1) {
        cashbackHistCurrentPage = page;
        try {
            const res = await fetch(`${BASE_URL}/api/cashback/history?page=${cashbackHistCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                cashbackHistTotalPages = data.total_pages || 1;

                const elCurr = document.getElementById('cashback-history-curr-page');
                const elTotal = document.getElementById('cashback-history-total-pages');
                const elItems = document.getElementById('cashback-history-total-items');
                const prevBtn = document.getElementById('cashback-history-prev-btn');
                const nextBtn = document.getElementById('cashback-history-next-btn');

                if (elCurr) elCurr.textContent = cashbackHistCurrentPage;
                if (elTotal) elTotal.textContent = cashbackHistTotalPages;
                if (elItems) elItems.textContent = data.total || 0;

                if (prevBtn) prevBtn.disabled = (cashbackHistCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (cashbackHistCurrentPage >= cashbackHistTotalPages);

                renderCashbackTable('cashback-history-body', data.items || []);
            }
        } catch (e) {
            console.error('Cashback history error:', e);
        }
    }

    const prevCbHistBtn = document.getElementById('cashback-history-prev-btn');
    const nextCbHistBtn = document.getElementById('cashback-history-next-btn');
    if (prevCbHistBtn) prevCbHistBtn.addEventListener('click', () => { if (cashbackHistCurrentPage > 1) loadCashbackHistory(cashbackHistCurrentPage - 1); });
    if (nextCbHistBtn) nextCbHistBtn.addEventListener('click', () => { if (cashbackHistCurrentPage < cashbackHistTotalPages) loadCashbackHistory(cashbackHistCurrentPage + 1); });

    // Pending Cashback
    let cashbackPendingCurrentPage = 1;
    let cashbackPendingTotalPages = 1;

    async function loadPendingCashback(page = 1) {
        cashbackPendingCurrentPage = page;
        try {
            const res = await fetch(`${BASE_URL}/api/cashback/pending?page=${cashbackPendingCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                cashbackPendingTotalPages = data.total_pages || 1;

                const elCurr = document.getElementById('cashback-pending-curr-page');
                const elTotal = document.getElementById('cashback-pending-total-pages');
                const elItems = document.getElementById('cashback-pending-total-items');
                const prevBtn = document.getElementById('cashback-pending-prev-btn');
                const nextBtn = document.getElementById('cashback-pending-next-btn');

                if (elCurr) elCurr.textContent = cashbackPendingCurrentPage;
                if (elTotal) elTotal.textContent = cashbackPendingTotalPages;
                if (elItems) elItems.textContent = data.total || 0;

                if (prevBtn) prevBtn.disabled = (cashbackPendingCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (cashbackPendingCurrentPage >= cashbackPendingTotalPages);

                renderCashbackTable('cashback-pending-body', data.items || []);
            }
        } catch (e) { console.error('Pending cashback error:', e); }
    }

    const prevCbPendBtn = document.getElementById('cashback-pending-prev-btn');
    const nextCbPendBtn = document.getElementById('cashback-pending-next-btn');
    if (prevCbPendBtn) prevCbPendBtn.addEventListener('click', () => { if (cashbackPendingCurrentPage > 1) loadPendingCashback(cashbackPendingCurrentPage - 1); });
    if (nextCbPendBtn) nextCbPendBtn.addEventListener('click', () => { if (cashbackPendingCurrentPage < cashbackPendingTotalPages) loadPendingCashback(cashbackPendingCurrentPage + 1); });

    // Approved Cashback
    let cashbackApprovedCurrentPage = 1;
    let cashbackApprovedTotalPages = 1;

    async function loadApprovedCashback(page = 1) {
        cashbackApprovedCurrentPage = page;
        try {
            const res = await fetch(`${BASE_URL}/api/cashback/approved?page=${cashbackApprovedCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                cashbackApprovedTotalPages = data.total_pages || 1;

                const elCurr = document.getElementById('cashback-approved-curr-page');
                const elTotal = document.getElementById('cashback-approved-total-pages');
                const elItems = document.getElementById('cashback-approved-total-items');
                const prevBtn = document.getElementById('cashback-approved-prev-btn');
                const nextBtn = document.getElementById('cashback-approved-next-btn');

                if (elCurr) elCurr.textContent = cashbackApprovedCurrentPage;
                if (elTotal) elTotal.textContent = cashbackApprovedTotalPages;
                if (elItems) elItems.textContent = data.total || 0;

                if (prevBtn) prevBtn.disabled = (cashbackApprovedCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (cashbackApprovedCurrentPage >= cashbackApprovedTotalPages);

                renderCashbackTable('cashback-approved-body', data.items || []);
            }
        } catch (e) { console.error('Approved cashback error:', e); }
    }

    const prevCbAppBtn = document.getElementById('cashback-approved-prev-btn');
    const nextCbAppBtn = document.getElementById('cashback-approved-next-btn');
    if (prevCbAppBtn) prevCbAppBtn.addEventListener('click', () => { if (cashbackApprovedCurrentPage > 1) loadApprovedCashback(cashbackApprovedCurrentPage - 1); });
    if (nextCbAppBtn) nextCbAppBtn.addEventListener('click', () => { if (cashbackApprovedCurrentPage < cashbackApprovedTotalPages) loadApprovedCashback(cashbackApprovedCurrentPage + 1); });

    function renderCashbackTable(targetBodyId, items) {
        const body = document.getElementById(targetBodyId);
        if (!body) return;
        if (items.length === 0) {
            body.innerHTML = '<tr><td colspan="6" class="empty-msg">No conversion records found.</td></tr>';
            return;
        }

        body.innerHTML = items.map(item => `
            <tr>
                <td>${formatLocalDateTime(item.created_at)}</td>
                <td><strong>${escapeHtml(item.merchant || 'Shopee')}</strong></td>
                <td><code>${escapeHtml(item.order_id || item.conversion_id)}</code></td>
                <td class="tabular-nums">₱${parseFloat(item.commission).toFixed(2)}</td>
                <td style="color: var(--color-success-text); font-weight: 700;" class="tabular-nums">₱${parseFloat(item.cashback).toFixed(2)}</td>
                <td><span class="badge ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></td>
            </tr>
        `).join('');
    }

    // --- Withdrawal Modal ---
    if (openWithdrawBtn) openWithdrawBtn.addEventListener('click', () => withdrawModal.classList.remove('hidden'));
    if (closeWithdrawBtn) closeWithdrawBtn.addEventListener('click', () => withdrawModal.classList.add('hidden'));

    if (withdrawForm) {
        withdrawForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const amount = parseFloat(document.getElementById('withdraw-amount').value);
            const account = document.getElementById('withdraw-account').value;

            try {
                const res = await fetch(`${BASE_URL}/api/wallet/withdraw`, {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({ amount, bank_account: account, payment_method: 'GCash / Bank' })
                });

                if (res.ok) {
                    showToast('Withdrawal request submitted successfully! Pending admin approval.', 'success');
                    withdrawModal.classList.add('hidden');
                    loadWalletData();
                } else {
                    const err = await res.json();
                    showToast(err.detail || 'Withdrawal failed', 'error');
                }
            } catch (e) {
                showToast('Connection error during withdrawal', 'error');
            }
        });
    }

    // --- Admin Data ---
    let allAdminLinks = [];
    let adminUsersCurrentPage = 1;
    let adminUsersTotalPages = 1;
    let adminLinksCurrentPage = 1;
    let adminLinksTotalPages = 1;
    let adminConversionsCurrentPage = 1;
    let adminConversionsTotalPages = 1;

    async function loadAdminUsers(page = 1) {
        adminUsersCurrentPage = page;
        try {
            const uRes = await fetch(`${BASE_URL}/api/admin/users?page=${adminUsersCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (uRes.ok) {
                const uData = await uRes.json();
                adminUsersTotalPages = uData.total_pages || 1;

                const elCurr = document.getElementById('admin-users-curr-page');
                const elTotal = document.getElementById('admin-users-total-pages');
                const elItems = document.getElementById('admin-users-total-items');
                const prevBtn = document.getElementById('admin-users-prev-btn');
                const nextBtn = document.getElementById('admin-users-next-btn');

                if (elCurr) elCurr.textContent = adminUsersCurrentPage;
                if (elTotal) elTotal.textContent = adminUsersTotalPages;
                if (elItems) elItems.textContent = uData.total || 0;

                if (prevBtn) prevBtn.disabled = (adminUsersCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (adminUsersCurrentPage >= adminUsersTotalPages);

                renderAdminUsers(uData.items || []);
            }
        } catch (e) { console.error('Admin users error:', e); }
    }

    async function loadAdminLinks(page = 1) {
        adminLinksCurrentPage = page;
        try {
            const lRes = await fetch(`${BASE_URL}/api/admin/links?page=${adminLinksCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (lRes.ok) {
                const lData = await lRes.json();
                allAdminLinks = lData.items || [];
                adminLinksTotalPages = lData.total_pages || 1;

                const elCurr = document.getElementById('admin-links-curr-page');
                const elTotal = document.getElementById('admin-links-total-pages');
                const elItems = document.getElementById('admin-links-total-items');
                const prevBtn = document.getElementById('admin-links-prev-btn');
                const nextBtn = document.getElementById('admin-links-next-btn');

                if (elCurr) elCurr.textContent = adminLinksCurrentPage;
                if (elTotal) elTotal.textContent = adminLinksTotalPages;
                if (elItems) elItems.textContent = lData.total || 0;

                if (prevBtn) prevBtn.disabled = (adminLinksCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (adminLinksCurrentPage >= adminLinksTotalPages);

                renderAdminLinks(allAdminLinks);
            }
        } catch (e) { console.error('Admin links error:', e); }
    }

    async function loadAdminConversions(page = 1) {
        adminConversionsCurrentPage = page;
        try {
            const cRes = await fetch(`${BASE_URL}/api/admin/conversions?page=${adminConversionsCurrentPage}&limit=20`, { headers: getAuthHeaders() });
            if (cRes.ok) {
                const cData = await cRes.json();
                adminConversionsTotalPages = cData.total_pages || 1;

                const elCurr = document.getElementById('admin-conversions-curr-page');
                const elTotal = document.getElementById('admin-conversions-total-pages');
                const elItems = document.getElementById('admin-conversions-total-items');
                const prevBtn = document.getElementById('admin-conversions-prev-btn');
                const nextBtn = document.getElementById('admin-conversions-next-btn');

                if (elCurr) elCurr.textContent = adminConversionsCurrentPage;
                if (elTotal) elTotal.textContent = adminConversionsTotalPages;
                if (elItems) elItems.textContent = cData.total || 0;

                if (prevBtn) prevBtn.disabled = (adminConversionsCurrentPage <= 1);
                if (nextBtn) nextBtn.disabled = (adminConversionsCurrentPage >= adminConversionsTotalPages);

                renderAdminConversions(cData.items || []);
            }
        } catch (e) { console.error('Admin conversions error:', e); }
    }

    const prevAdminUsersBtn = document.getElementById('admin-users-prev-btn');
    const nextAdminUsersBtn = document.getElementById('admin-users-next-btn');
    if (prevAdminUsersBtn) prevAdminUsersBtn.addEventListener('click', () => { if (adminUsersCurrentPage > 1) loadAdminUsers(adminUsersCurrentPage - 1); });
    if (nextAdminUsersBtn) nextAdminUsersBtn.addEventListener('click', () => { if (adminUsersCurrentPage < adminUsersTotalPages) loadAdminUsers(adminUsersCurrentPage + 1); });

    const prevAdminLinksBtn = document.getElementById('admin-links-prev-btn');
    const nextAdminLinksBtn = document.getElementById('admin-links-next-btn');
    if (prevAdminLinksBtn) prevAdminLinksBtn.addEventListener('click', () => { if (adminLinksCurrentPage > 1) loadAdminLinks(adminLinksCurrentPage - 1); });
    if (nextAdminLinksBtn) nextAdminLinksBtn.addEventListener('click', () => { if (adminLinksCurrentPage < adminLinksTotalPages) loadAdminLinks(adminLinksCurrentPage + 1); });

    const prevAdminConvBtn = document.getElementById('admin-conversions-prev-btn');
    const nextAdminConvBtn = document.getElementById('admin-conversions-next-btn');
    if (prevAdminConvBtn) prevAdminConvBtn.addEventListener('click', () => { if (adminConversionsCurrentPage > 1) loadAdminConversions(adminConversionsCurrentPage - 1); });
    if (nextAdminConvBtn) nextAdminConvBtn.addEventListener('click', () => { if (adminConversionsCurrentPage < adminConversionsTotalPages) loadAdminConversions(adminConversionsCurrentPage + 1); });

    async function loadAdminData() {
        try {
            await loadAdminUsers(1);
            await loadAdminLinks(1);
            await loadAdminConversions(1);

            const wRes = await fetch(`${BASE_URL}/api/admin/withdrawals`, { headers: getAuthHeaders() });
            if (wRes.ok) {
                const wData = await wRes.json();
                renderAdminWithdrawals(wData.items || []);
            }
        } catch (e) {
            console.error('Admin data error:', e);
        }
    }

    function renderAdminUsers(users) {
        const body = document.getElementById('admin-users-body');
        if (!body) return;
        if (users.length === 0) {
            body.innerHTML = '<tr><td colspan="9" class="empty-msg">No registered users found.</td></tr>';
            return;
        }

        body.innerHTML = users.map(u => `
            <tr>
                <td>#${u.id}</td>
                <td><strong>${escapeHtml(u.name)}</strong></td>
                <td>${escapeHtml(u.email)}</td>
                <td><span class="badge ${u.role === 'admin' ? 'approved' : 'pending'}">${escapeHtml(u.role)}</span></td>
                <td><strong class="tabular-nums" style="color: var(--color-fin-estimated-text);">₱${parseFloat(u.estimated_cashback || 0).toFixed(2)}</strong></td>
                <td><span class="badge pending tabular-nums">₱${parseFloat(u.wallet_pending || 0).toFixed(2)}</span></td>
                <td><span class="badge approved tabular-nums">₱${parseFloat(u.wallet_balance || 0).toFixed(2)}</span></td>
                <td><strong class="tabular-nums" style="color: var(--color-fin-paid-text);">₱${parseFloat(u.wallet_paid || 0).toFixed(2)}</strong></td>
                <td>
                    <button class="action-btn alt-btn view-user-activity-btn" data-userid="${u.id}" data-username="${escapeHtml(u.name)}" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; height: auto;">
                        🔍 View Links
                    </button>
                </td>
            </tr>
        `).join('');

        document.querySelectorAll('.view-user-activity-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const userId = btn.getAttribute('data-userid');
                const userName = btn.getAttribute('data-username');
                openAdminUserLinksModal(userId, userName);
            });
        });
    }

    const adminLinksSearchInput = document.getElementById('admin-links-search');
    if (adminLinksSearchInput) {
        adminLinksSearchInput.addEventListener('input', () => {
            const query = adminLinksSearchInput.value.toLowerCase().trim();
            const filtered = allAdminLinks.filter(l => 
                (l.original_url && l.original_url.toLowerCase().includes(query)) ||
                (l.tracking_id && l.tracking_id.toLowerCase().includes(query)) ||
                (l.user_name && l.user_name.toLowerCase().includes(query))
            );
            renderAdminLinks(filtered);
        });
    }

    let currentUserModalLinks = [];

    async function openAdminUserLinksModal(userId, userName) {
        const modal = document.getElementById('admin-user-links-modal');
        const titleEl = document.getElementById('modal-user-links-title');
        const subEl = document.getElementById('modal-user-links-sub');
        const body = document.getElementById('user-modal-links-body');

        if (titleEl) titleEl.innerHTML = `Activity Breakdown: <span style="color: var(--color-primary); font-weight: 800;">${userName}</span>`;
        if (subEl) subEl.textContent = `Tracking generated links, pending validations, and payouts for User #${userId} (${userName}).`;

        if (body) body.innerHTML = '<tr><td colspan="6" class="empty-msg">Loading user links...</td></tr>';
        if (modal) modal.classList.remove('hidden');

        try {
            const res = await fetch(`${BASE_URL}/api/admin/users/${userId}/links`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                currentUserModalLinks = data.items || [];
                renderUserLinksModalContent(currentUserModalLinks, 'all');
            } else {
                if (body) body.innerHTML = '<tr><td colspan="6" class="empty-msg">Failed to load user links.</td></tr>';
            }
        } catch (e) {
            console.error('Error fetching user links:', e);
            if (body) body.innerHTML = '<tr><td colspan="6" class="empty-msg">Connection error.</td></tr>';
        }
    }

    function renderUserLinksModalContent(links, activeFilter = 'all') {
        const body = document.getElementById('user-modal-links-body');
        
        let genCnt = 0, genSum = 0;
        let pendCnt = 0, pendSum = 0;
        let appCnt = 0, appSum = 0;
        let paidCnt = 0, paidSum = 0;

        links.forEach(l => {
            const st = (l.status || 'generated').toLowerCase();
            const val = parseFloat(l.cashback_amount || 5.00);

            if (st === 'generated') {
                genCnt++;
                genSum += val;
            } else if (st === 'pending' || st === 'tracked') {
                pendCnt++;
                pendSum += val;
            } else if (st === 'approved' || st === 'available' || st === 'validated') {
                appCnt++;
                appSum += val;
            } else if (st === 'paid') {
                paidCnt++;
                paidSum += val;
            } else {
                genCnt++;
                genSum += val;
            }
        });

        const elGenCnt = document.getElementById('u-modal-cnt-gen');
        const elGenSum = document.getElementById('u-modal-sum-gen');
        const elPendCnt = document.getElementById('u-modal-cnt-pending');
        const elPendSum = document.getElementById('u-modal-sum-pending');
        const elAppCnt = document.getElementById('u-modal-cnt-approved');
        const elAppSum = document.getElementById('u-modal-sum-approved');
        const elPaidCnt = document.getElementById('u-modal-cnt-paid');
        const elPaidSum = document.getElementById('u-modal-sum-paid');

        if (elGenCnt) elGenCnt.textContent = `${genCnt} link${genCnt !== 1 ? 's' : ''}`;
        if (elGenSum) elGenSum.textContent = `₱${genSum.toFixed(2)}`;
        if (elPendCnt) elPendCnt.textContent = `${pendCnt} link${pendCnt !== 1 ? 's' : ''}`;
        if (elPendSum) elPendSum.textContent = `₱${pendSum.toFixed(2)}`;
        if (elAppCnt) elAppCnt.textContent = `${appCnt} link${appCnt !== 1 ? 's' : ''}`;
        if (elAppSum) elAppSum.textContent = `₱${appSum.toFixed(2)}`;
        if (elPaidCnt) elPaidCnt.textContent = `${paidCnt} link${paidCnt !== 1 ? 's' : ''}`;
        if (elPaidSum) elPaidSum.textContent = `₱${paidSum.toFixed(2)}`;

        const filtered = links.filter(l => {
            const st = (l.status || 'generated').toLowerCase();
            if (activeFilter === 'all') return true;
            if (activeFilter === 'generated') return st === 'generated';
            if (activeFilter === 'pending') return st === 'pending' || st === 'tracked';
            if (activeFilter === 'approved') return st === 'approved' || st === 'available' || st === 'validated';
            if (activeFilter === 'paid') return st === 'paid';
            return true;
        });

        if (!body) return;
        if (filtered.length === 0) {
            body.innerHTML = `<tr><td colspan="6" class="empty-msg">No ${activeFilter} links found for this user.</td></tr>`;
            return;
        }

        body.innerHTML = filtered.map(l => {
            const statusClass = (l.status || 'generated').toLowerCase();
            const val = parseFloat(l.cashback_amount || 5.00);
            return `
                <tr>
                    <td>${new Date(l.created_at).toLocaleDateString()} ${new Date(l.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</td>
                    <td><code>${l.tracking_id.substring(0, 8)}...</code></td>
                    <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <a href="${l.deeplink}" target="_blank" style="color: var(--color-primary); text-decoration: none;">🔗 ${l.original_url}</a>
                    </td>
                    <td><strong class="tabular-nums" style="color: var(--color-success-text);">₱${val.toFixed(2)}</strong></td>
                    <td><span class="badge ${statusClass}">${l.status || 'Generated'}</span></td>
                    <td>
                        <button class="action-btn alt-btn modal-track-btn" data-tracking="${l.tracking_id}" data-status="${statusClass}" data-url="${l.original_url}" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; height: auto;">
                            Timeline ⏱️
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        body.querySelectorAll('.modal-track-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const trackingId = btn.getAttribute('data-tracking');
                const status = btn.getAttribute('data-status');
                const originalUrl = btn.getAttribute('data-url');
                openTimelineModal(trackingId, status, originalUrl);
            });
        });
    }

    const closeUserLinksModalBtn = document.getElementById('close-user-links-modal-btn');
    const userLinksModal = document.getElementById('admin-user-links-modal');
    if (closeUserLinksModalBtn && userLinksModal) {
        closeUserLinksModalBtn.addEventListener('click', () => userLinksModal.classList.add('hidden'));
    }

    document.querySelectorAll('.user-link-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.user-link-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');
            renderUserLinksModalContent(currentUserModalLinks, filter);
        });
    });

    function renderAdminLinks(links) {
        const body = document.getElementById('admin-links-body');
        if (!body) return;
        if (links.length === 0) {
            body.innerHTML = '<tr><td colspan="12" class="empty-msg">No links generated yet.</td></tr>';
            return;
        }

        body.innerHTML = links.map(l => `
            <tr>
                <td>#${l.id}</td>
                <td><strong>${escapeHtml(l.user_name || 'John Cashback')}</strong></td>
                <td>User #${l.user_id}</td>
                <td><code>${escapeHtml(l.tracking_id)}</code></td>
                <td>${escapeHtml(l.aff_sub2 || ('User #' + l.user_id))}</td>
                <td>${escapeHtml(l.aff_sub3 || 'shopback')}</td>
                <td>${escapeHtml(l.aff_sub4 || 'web')}</td>
                <td>${escapeHtml(l.aff_sub5 || 'v2.0')}</td>
                <td><span class="badge approved">${l.clicks || 0} clicks</span></td>
                <td><a href="${escapeHtml(l.deeplink)}" target="_blank" style="color: var(--color-primary); text-decoration: none;">View Deeplink 🔗</a></td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(l.original_url)}">${escapeHtml(l.original_url)}</td>
                <td>${formatLocalDateTime(l.created_at)}</td>
            </tr>
        `).join('');
    }

    function renderAdminWithdrawals(withdrawals) {
        const body = document.getElementById('admin-withdrawals-body');
        if (!body) return;
        const pendingW = withdrawals.filter(w => w.status === 'Pending');
        
        if (pendingW.length === 0) {
            body.innerHTML = '<tr><td colspan="6" class="empty-msg">No pending withdrawal requests.</td></tr>';
            return;
        }

        body.innerHTML = pendingW.map(w => `
            <tr>
                <td>#${w.id}</td>
                <td>User #${w.user_id}</td>
                <td style="font-weight: 700;" class="tabular-nums">₱${parseFloat(w.amount).toFixed(2)}</td>
                <td>${w.bank_account || w.payment_method}</td>
                <td>${new Date(w.requested_at).toLocaleDateString()}</td>
                <td>
                    <button class="nav-btn approve-w-btn" data-id="${w.id}">Approve</button>
                    <button class="nav-btn reject-w-btn" data-id="${w.id}" style="background: var(--color-danger-bg); color: var(--color-danger-text); border-color: var(--color-danger-border);">Reject</button>
                </td>
            </tr>
        `).join('');

        document.querySelectorAll('.approve-w-btn').forEach(btn => {
            btn.addEventListener('click', () => processWithdrawalAction(btn.dataset.id, 'approve'));
        });
        document.querySelectorAll('.reject-w-btn').forEach(btn => {
            btn.addEventListener('click', () => processWithdrawalAction(btn.dataset.id, 'reject'));
        });
    }

    async function processWithdrawalAction(withdrawal_id, action) {
        const endpoint = action === 'approve' ? '/api/admin/approve-withdrawal' : '/api/admin/reject-withdrawal';
        try {
            const res = await fetch(`${BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ withdrawal_id: parseInt(withdrawal_id) })
            });

            if (res.ok) {
                showToast(`Withdrawal request #${withdrawal_id} ${action}d!`, 'success');
                loadAdminData();
            } else {
                const err = await res.json();
                showToast(err.detail || 'Action failed', 'error');
            }
        } catch (e) {
            showToast('Connection error', 'error');
        }
    }

    function renderAdminConversions(conversions) {
        const body = document.getElementById('admin-conversions-body');
        if (!body) return;
        if (conversions.length === 0) {
            body.innerHTML = '<tr><td colspan="10" class="empty-msg">No conversions recorded yet.</td></tr>';
            return;
        }

        body.innerHTML = conversions.map(c => `
            <tr>
                <td><strong>${escapeHtml(c.conversion_id)}</strong></td>
                <td><code>${escapeHtml(c.order_id || '-')}</code></td>
                <td>User #${c.user_id}</td>
                <td>${escapeHtml(c.merchant || 'Shopee')}</td>
                <td style="font-weight: 600;" class="tabular-nums">₱${parseFloat(c.commission).toFixed(2)}</td>
                <td style="color: var(--color-warning-text); font-weight: 600;" class="tabular-nums">₱${parseFloat(c.cashback).toFixed(2)}</td>
                <td style="color: var(--color-success-text); font-weight: 700;" class="tabular-nums">₱${parseFloat(c.admin_profit || (c.commission - c.cashback)).toFixed(2)}</td>
                <td><code>${escapeHtml(c.tracking_id || c.aff_sub1 || '-')}</code></td>
                <td><span class="badge ${escapeHtml(c.status)}">${escapeHtml(c.status)}</span></td>
                <td>${formatLocalDateTime(c.created_at)}</td>
            </tr>
        `).join('');
    }

    // --- Test Conversion Modal ---
    if (openTestConvBtn) openTestConvBtn.addEventListener('click', () => testConvModal.classList.remove('hidden'));
    if (closeTestConvBtn) closeTestConvBtn.addEventListener('click', () => testConvModal.classList.add('hidden'));

    if (testConvForm) {
        testConvForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tracking_id = document.getElementById('sim-tracking-id').value;
            const merchant = document.getElementById('sim-merchant').value;
            const commission = parseFloat(document.getElementById('sim-commission').value);
            const status = document.getElementById('sim-status').value;

            const payload = {
                conversion_id: `CONV_${Math.floor(Math.random()*1000000)}`,
                order_id: `SP_${Math.floor(Math.random()*1000000)}`,
                status: status,
                commission: commission,
                merchant: merchant,
                aff_sub1: tracking_id
            };

            try {
                const res = await fetch(`${BASE_URL}/api/admin/manual-conversion`, {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    const data = await res.json();
                    showToast(`Test conversion triggered! Cashback: ₱${parseFloat(data.cashback).toFixed(2)}`, 'success');
                    testConvModal.classList.add('hidden');
                    loadAdminData();
                    loadWalletData();
                } else {
                    const err = await res.json();
                    showToast(err.detail || 'Trigger failed', 'error');
                }
            } catch (e) {
                showToast('Connection error', 'error');
            }
        });
    }

    // --- Link Generator Logic ---
    function updateTimelineStepper(stage) {
        const box = document.getElementById('timeline-stepper-box');
        if (!box) return;
        box.classList.remove('hidden');

        for (let i = 1; i <= 5; i++) {
            const node = document.getElementById(`step-node-${i}`);
            const line = document.getElementById(`step-line-${i}`);
            if (node) {
                node.classList.remove('active', 'done');
                if (i < stage) node.classList.add('done');
                if (i === stage) node.classList.add('active');
            }
            if (line) {
                line.classList.remove('active');
                if (i < stage) line.classList.add('active');
            }
        }
    }

    function renderPreview(previewData) {
        previewTitle.textContent = previewData.title || 'Product Link';
        if (previewData.image) {
            previewImage.src = previewData.image;
            previewImage.classList.remove('hidden');
        } else {
            previewImage.classList.add('hidden');
        }
        
        const cashbackBadge = document.getElementById('cashback-rate-badge');
        if (cashbackBadge) {
            const cbAmount = previewData.estimated_cashback ? parseFloat(previewData.estimated_cashback).toFixed(2) : "5.00";
            const commAmount = previewData.estimated_commission ? parseFloat(previewData.estimated_commission).toFixed(2) : "25.00";
            cashbackBadge.innerHTML = `✨ <strong>Estimated Cashback: ₱${cbAmount}</strong> <span style="font-weight: normal; opacity: 0.85;">(10% of ₱${commAmount} total commission)</span>`;
            cashbackBadge.classList.remove('hidden');
        }

        updateTimelineStepper(1);
        previewContainer.classList.remove('hidden');
        previewContainer.style.display = 'flex';

        if (currentGeneratedItem) {
            if (previewData.title) currentGeneratedItem.title = cleanProductTitle(previewData.title, currentGeneratedItem.url);
            if (previewData.image) currentGeneratedItem.image = previewData.image;
            if (previewData.estimated_cashback) currentGeneratedItem.cashback_amount = parseFloat(previewData.estimated_cashback).toFixed(2);
        }
    }

    function fetchAndRenderPreview(url) {
        fetch(`${BASE_URL}/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        })
        .then(res => res.json())
        .then(previewData => {
            localStorage.setItem('preview_' + url, JSON.stringify(previewData));
            renderPreview(previewData);
        })
        .catch(err => console.error("Preview fetch failed:", err));
    }

    // Restore state on reload
    const currentUrl = localStorage.getItem('current_url');
    if (currentUrl) {
        const cachedLink = localStorage.getItem('link_' + currentUrl);
        const cachedTrackingId = localStorage.getItem('tracking_' + currentUrl);
        if (cachedLink) {
            urlInput.value = currentUrl;
            showSuccess(cachedLink);
            checkoutBtn.href = cachedLink;
            checkoutBtn.dataset.trackingId = cachedTrackingId || '';
            
            setCurrentItem(currentUrl, cachedLink, cachedTrackingId);
            const cachedPreview = localStorage.getItem('preview_' + currentUrl);
            if (cachedPreview) {
                const parsed = JSON.parse(cachedPreview);
                renderPreview(parsed);
                if (currentGeneratedItem) {
                    if (parsed.title) currentGeneratedItem.title = parsed.title;
                    if (parsed.image) currentGeneratedItem.image = parsed.image;
                }
            } else {
                fetchAndRenderPreview(currentUrl);
            }
        }
    }

    // Clipboard Paste Handler
    const pasteBtn = document.getElementById('paste-btn');
    if (pasteBtn) {
        pasteBtn.addEventListener('click', async () => {
            try {
                if (navigator.clipboard && navigator.clipboard.readText) {
                    const text = await navigator.clipboard.readText();
                    if (text && text.trim()) {
                        urlInput.value = text.trim();
                        urlInput.focus();
                        showToast('Link pasted from clipboard!', 'info');
                    } else {
                        showToast('Your clipboard is empty. Copy a product link first.', 'warning');
                    }
                } else {
                    showToast('Clipboard access unavailable. Please paste manually.', 'warning');
                }
            } catch (err) {
                showToast('Clipboard permission needed to auto-paste.', 'warning');
            }
        });
    }

    // Copy Button Handler with visual feedback + Toast
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const linkText = affiliateLinkInput.value;
            if (!linkText) return;

            try {
                await navigator.clipboard.writeText(linkText);
                if (copyBtnText) copyBtnText.textContent = 'Copied! ✓';
                copyBtn.style.background = 'var(--color-success)';
                copyBtn.style.borderColor = 'var(--color-success)';
                showToast('Affiliate link copied to clipboard!', 'success');

                setTimeout(() => {
                    if (copyBtnText) copyBtnText.textContent = 'Copy';
                    copyBtn.style.background = '';
                    copyBtn.style.borderColor = '';
                }, 2500);
            } catch (err) {
                affiliateLinkInput.select();
                document.execCommand('copy');
                showToast('Link copied to clipboard!', 'success');
            }
        });
    }

    // Form Submit / Generate Link Handler
    async function handleGenerateLink() {
        let url = urlInput.value.trim();
        if (!url) {
            showToast('Please enter a product URL.', 'warning');
            return showError('Please enter a product URL.');
        }

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
            urlInput.value = url;
        }


        setLoading(true);
        hideResult();

        // Check Cache first (ignore stale demo invl.me links)
        const cachedLink = localStorage.getItem('link_' + url);
        const cachedTrackingId = localStorage.getItem('tracking_' + url);
        if (cachedLink && !cachedLink.includes('invl.me') && !cachedLink.includes('involve.asia')) {
            localStorage.setItem('current_url', url);
            showSuccess(cachedLink);
            checkoutBtn.href = cachedTrackingId ? `${BASE_URL}/r/${cachedTrackingId}` : cachedLink;

            
            setCurrentItem(url, cachedLink, cachedTrackingId);

            const cachedPreview = localStorage.getItem('preview_' + url);
            if (cachedPreview) {
                const parsed = JSON.parse(cachedPreview);
                renderPreview(parsed);
                if (currentGeneratedItem) {
                    if (parsed.title) currentGeneratedItem.title = parsed.title;
                    if (parsed.image) currentGeneratedItem.image = parsed.image;
                }
            } else {
                fetchAndRenderPreview(url);
            }
            
            setLoading(false);
            showToast('Retrieved cached tracking link!', 'info');
            return;
        }

        try {
            const response = await fetch(`${BASE_URL}/api/affiliate/generate`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ product_url: url })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                localStorage.setItem('current_url', url);
                localStorage.setItem('link_' + url, data.deeplink);
                localStorage.setItem('tracking_' + url, data.tracking_id);
                showSuccess(data.deeplink);
                
                const cashbackBadge = document.getElementById('cashback-rate-badge');
                const cashbackVal = document.getElementById('cashback-rate-val');
                if (cashbackBadge && data.cashback_rate) {
                    if (cashbackVal) cashbackVal.textContent = data.cashback_rate;
                    cashbackBadge.classList.remove('hidden');
                }

                checkoutBtn.href = data.deeplink;
                checkoutBtn.dataset.trackingId = data.tracking_id;

                setCurrentItem(url, data.deeplink, data.tracking_id);

                const simTrk = document.getElementById('sim-tracking-id');
                if (simTrk) simTrk.value = data.tracking_id;

                fetchAndRenderPreview(url);
                setLoading(false);
                showToast('Tracking link generated successfully! ✨', 'success');
            } else {
                showError(data.detail || data.message || 'Failed to generate link.');
                showToast(data.detail || data.message || 'Failed to generate link', 'error');
                setLoading(false);
            }
        } catch (error) {
            showError('Could not connect to the server.');
            showToast('Could not connect to the server.', 'error');
            setLoading(false);
        }
    }

    if (generatorForm) {
        generatorForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleGenerateLink();
        });
    } else if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerateLink);
    }

    // Click Tracker Handler
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            const trackingId = checkoutBtn.dataset.trackingId;
            if (trackingId) {
                const trackUrl = `${BASE_URL}/api/affiliate/track-click/${trackingId}`;
                try {
                    if (navigator.sendBeacon) {
                        navigator.sendBeacon(trackUrl);
                    }
                } catch (e) {}

                fetch(trackUrl, { method: 'POST', keepalive: true })
                    .then(() => setTimeout(loadAdminData, 400))
                    .catch(e => console.error("Click track error:", e));

                setTimeout(loadAdminData, 600);
            }
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            localStorage.removeItem('current_url');
            urlInput.value = '';
            const formEl = generatorForm || inputSection;
            if (formEl) {
                formEl.classList.remove('hidden');
                formEl.style.display = 'flex';
            }
            hideResult();
            setLoading(false);
            urlInput.focus();
        });
    }

    function setLoading(isLoading) {
        if (isLoading) {
            if (btnText) btnText.classList.add('hidden');
            if (loader) loader.classList.remove('hidden');
            if (generateBtn) generateBtn.disabled = true;
        } else {
            if (btnText) btnText.classList.remove('hidden');
            if (loader) loader.classList.add('hidden');
            if (generateBtn) generateBtn.disabled = false;
        }
    }

    function hideResult() {
        if (resultSection) {
            resultSection.classList.add('hidden');
            resultSection.style.display = 'none';
        }
        if (errorMessage) {
            errorMessage.classList.add('hidden');
            errorMessage.style.display = 'none';
        }
        if (successMessage) {
            successMessage.classList.add('hidden');
            successMessage.style.display = 'none';
        }
        if (previewContainer) {
            previewContainer.classList.add('hidden');
            previewContainer.style.display = 'none';
        }
    }

    function showError(message) {
        const formEl = generatorForm || inputSection;
        if (formEl) {
            formEl.classList.remove('hidden');
            formEl.style.display = 'flex';
        }
        if (resultSection) {
            resultSection.classList.remove('hidden');
            resultSection.style.display = 'block';
        }
        if (errorMessage) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
            errorMessage.style.display = 'block';
        }
    }

    function showSuccess(link) {
        const formEl = generatorForm || inputSection;
        if (formEl) {
            formEl.classList.add('hidden');
            formEl.style.display = 'none';
        }
        if (resultSection) {
            resultSection.classList.remove('hidden');
            resultSection.style.display = 'block';
        }
        if (affiliateLinkInput) affiliateLinkInput.value = link;
        if (successMessage) {
            successMessage.classList.remove('hidden');
            successMessage.style.display = 'flex';
        }
    }

    // Cashback Cart Logic
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', () => {
            if (!currentGeneratedItem) return;
            saveCartItem(currentGeneratedItem);
            addToCartBtn.textContent = '✅ Saved in Cart!';
            showToast('Product link saved to Cashback Cart!', 'success');
            setTimeout(() => { addToCartBtn.textContent = '🛒 Add to Cart'; }, 2500);
        });
    }

    function getCartItems() {
        try {
            return JSON.parse(localStorage.getItem('cashback_cart') || '[]');
        } catch (e) {
            return [];
        }
    }

    function saveCartItem(item) {
        const pImg = document.getElementById('preview-image');
        if ((!item.image || item.image.includes('unsplash')) && pImg && pImg.src && !pImg.classList.contains('hidden')) {
            item.image = pImg.src;
        }

        const pTitle = document.getElementById('preview-title');
        if ((!item.title || item.title === item.url) && pTitle && pTitle.textContent && pTitle.textContent !== 'Product Title') {
            item.title = pTitle.textContent;
        }

        let cart = getCartItems();
        if (!cart.some(c => c.tracking_id === item.tracking_id)) {
            if ((!item.image || !item.title || item.title === item.url) && item.url) {
                const cachedPreview = localStorage.getItem('preview_' + item.url);
                if (cachedPreview) {
                    try {
                        const parsed = JSON.parse(cachedPreview);
                        if (parsed.image) item.image = parsed.image;
                        if (parsed.title) item.title = parsed.title;
                    } catch (e) {}
                }
            }
            cart.unshift(item);
            localStorage.setItem('cashback_cart', JSON.stringify(cart));
            renderCartUI();
        }
    }

    function removeCartItem(trackingId) {
        let cart = getCartItems().filter(c => c.tracking_id !== trackingId);
        localStorage.setItem('cashback_cart', JSON.stringify(cart));
        renderCartUI();
        showToast('Item removed from cart', 'info');
    }

    function renderCartUI() {
        const container = document.getElementById('cart-items-container');
        const badge = document.getElementById('cart-count-badge');
        const cart = getCartItems();

        if (badge) badge.textContent = cart.length;
        if (!container) return;

        if (cart.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 3rem 1.5rem; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg);">
                    <div style="font-size: 3rem; margin-bottom: 0.75rem;">🛒</div>
                    <h3 style="font-size: 1.1rem; font-weight: 800; color: var(--color-text-primary); margin-bottom: 0.4rem;">Your Cashback Cart is Empty</h3>
                    <p style="font-size: 0.88rem; color: var(--color-text-muted); max-width: 420px; margin: 0 auto 1.25rem auto;">Paste Shopee, Lazada, or TikTok product links in the Link Generator & save them here for later checkout!</p>
                    <button class="action-btn" onclick="document.querySelector('[data-tab=\\'tab-generator\\']').click()" style="height: 42px; font-size: 0.88rem;">
                        Generate & Save Links ✨
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = cart.map(item => {
            const displayTitle = cleanProductTitle(item.title, item.url);
            const hasImage = item.image && item.image.trim().length > 0 && !item.image.includes('unsplash');
            
            const imgHtml = hasImage 
                ? `<img src="${item.image}" alt="Preview" style="width: 64px; height: 64px; object-fit: contain; border-radius: 8px; border: 1px solid var(--color-border); background: var(--color-bg); flex-shrink: 0;" />` 
                : `<div style="width: 64px; height: 64px; border-radius: 8px; border: 1px solid var(--color-border); background: var(--color-surface-secondary); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; flex-shrink: 0;">🛍️</div>`;

            return `
                <div class="card" style="background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 1.1rem 1.25rem; display: flex; align-items: center; justify-content: space-between; gap: 1.25rem; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 1rem; flex: 1; min-width: 260px;">
                        ${imgHtml}
                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem;">
                                <span class="badge available tabular-nums" style="font-size: 0.75rem;">₱${parseFloat(item.cashback_amount || 5).toFixed(2)} Cashback</span>
                                <span style="font-size: 0.72rem; color: var(--color-text-muted);">ID: <code style="color: var(--color-primary);">${item.tracking_id.substring(0, 8)}...</code></span>
                            </div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: var(--color-text-primary); margin: 0; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${displayTitle}</h4>
                        </div>
                    </div>
                    
                    <div style="display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0;">
                        <a href="${item.deeplink}" target="_blank" class="checkout-btn" style="height: 42px; font-size: 0.88rem; min-width: 170px;">
                            Proceed to Checkout 🛍️
                        </a>
                        <button class="nav-btn remove-cart-btn" data-tracking="${item.tracking_id}" title="Remove item" style="height: 42px; padding: 0 0.85rem; font-size: 0.8rem; color: var(--color-danger-text); border-color: var(--color-danger-border); background: var(--color-danger-bg);">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.remove-cart-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const trk = btn.getAttribute('data-tracking');
                removeCartItem(trk);
            });
        });
    }

    // Sub-Tabs Switching Handler
    document.querySelectorAll('.subtabs-nav').forEach(nav => {
        nav.querySelectorAll('.subtab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                nav.querySelectorAll('.subtab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const targetId = btn.getAttribute('data-subtab');
                const parentSection = nav.closest('.tab-content');
                if (parentSection) {
                    parentSection.querySelectorAll('.subtab-content').forEach(content => {
                        if (content.id === targetId) {
                            content.classList.remove('hidden');
                        } else {
                            content.classList.add('hidden');
                        }
                    });
                }
            });
        });
    });

    renderCartUI();

    // Initial Authentication Check
    checkAuth();
});
