document.addEventListener('DOMContentLoaded', () => {
    const BASE_URL = window.location.origin;

    const adminLoginView = document.getElementById('admin-login-view');
    const adminDashboardView = document.getElementById('admin-dashboard-view');
    const adminLoginForm = document.getElementById('admin-login-form');
    const adminLogoutBtn = document.getElementById('admin-logout-btn');
    const adminUserBadge = document.getElementById('admin-user-badge');

    let currentAdmin = null;

    function getAdminToken() {
        return localStorage.getItem('admin_access_token');
    }

    function getAdminAuthHeaders() {
        const token = getAdminToken();
        return token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
    }

    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `admin-toast ${type}`;
        const icon = type === 'error' ? '⚠️' : (type === 'success' ? '✅' : 'ℹ️');
        toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px) scale(0.95)';
            toast.style.transition = 'all 0.25s ease';
            setTimeout(() => toast.remove(), 250);
        }, 3500);
    }

    function showLoginAlert(message, type = 'error') {
        const banner = document.getElementById('admin-alert-banner');
        if (!banner) {
            showToast(message, type);
            return;
        }
        banner.className = `admin-alert-banner ${type}`;
        const icon = type === 'error' ? '❌' : '✅';
        banner.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
        banner.classList.remove('hidden');
    }

    function clearLoginAlert() {
        const banner = document.getElementById('admin-alert-banner');
        if (banner) banner.classList.add('hidden');
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

    // Check Admin Authentication
    async function checkAdminAuth() {
        const token = getAdminToken();
        if (!token) {
            showLoginView();
            return;
        }

        try {
            const res = await fetch(`${BASE_URL}/api/auth/me`, { headers: getAdminAuthHeaders() });
            if (res.ok) {
                const user = await res.json();
                if (user.role === 'admin') {
                    currentAdmin = user;
                    showDashboardView();
                    loadAdminData();
                } else {
                    showToast('Access denied: Account is not an administrator', 'error');
                    localStorage.removeItem('admin_access_token');
                    showLoginView();
                }
            } else {
                localStorage.removeItem('admin_access_token');
                showLoginView();
            }
        } catch (e) {
            console.error('Admin auth check error:', e);
            showLoginView();
        }
    }

    function showLoginView() {
        document.documentElement.classList.remove('admin-authed');
        if (adminLoginView) adminLoginView.classList.remove('hidden');
        if (adminDashboardView) adminDashboardView.classList.add('hidden');
    }

    function showDashboardView() {
        document.documentElement.classList.add('admin-authed');
        if (adminLoginView) adminLoginView.classList.add('hidden');
        if (adminDashboardView) adminDashboardView.classList.remove('hidden');
        if (adminUserBadge && currentAdmin) {
            adminUserBadge.textContent = `${currentAdmin.name} (${currentAdmin.email})`;
        }
    }

    // Admin Login Form Submit
    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearLoginAlert();
            const email = document.getElementById('admin-email').value.trim();
            const password = document.getElementById('admin-password').value;

            try {
                const res = await fetch(`${BASE_URL}/api/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (res.ok) {
                    const data = await res.json();
                    
                    // Verify if user is admin
                    const meRes = await fetch(`${BASE_URL}/api/auth/me`, {
                        headers: { 'Authorization': `Bearer ${data.access_token}` }
                    });

                    if (meRes.ok) {
                        const user = await meRes.json();
                        if (user.role === 'admin') {
                            localStorage.setItem('admin_access_token', data.access_token);
                            currentAdmin = user;
                            showToast(`Welcome back, ${user.name}!`, 'success');
                            showDashboardView();
                            loadAdminData();
                        } else {
                            showLoginAlert('Login failed: Account does not have admin privileges', 'error');
                        }
                    }
                } else {
                    showLoginAlert('Invalid admin email or password. Please check your credentials.', 'error');
                }
            } catch (err) {
                console.error('Admin login error:', err);
                showLoginAlert('Unable to connect to authentication server', 'error');
            }
        });
    }

    // Password Visibility Toggle
    const togglePassBtn = document.getElementById('toggle-admin-pass-btn');
    const adminPassInput = document.getElementById('admin-password');
    if (togglePassBtn && adminPassInput) {
        togglePassBtn.addEventListener('click', () => {
            const isPass = adminPassInput.type === 'password';
            adminPassInput.type = isPass ? 'text' : 'password';
            togglePassBtn.textContent = isPass ? '🙈' : '👁️';
        });
    }

    // Admin Logout
    if (adminLogoutBtn) {
        adminLogoutBtn.addEventListener('click', async () => {
            try {
                await fetch(`${BASE_URL}/api/auth/logout`, {
                    method: 'POST',
                    headers: getAdminAuthHeaders()
                });
            } catch (e) {}
            localStorage.removeItem('admin_access_token');
            currentAdmin = null;
            showToast('Admin session logged out cleanly', 'info');
            showLoginView();
        });
    }

    // Admin Subtabs Navigation
    const subtabButtons = document.querySelectorAll('.admin-tab-btn');
    subtabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');
            subtabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            document.querySelectorAll('.admin-tab-panel').forEach(content => {
                content.classList.add('hidden');
            });
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.remove('hidden');
        });
    });

    // Load Admin System Data
    async function loadAdminData() {
        try {
            await Promise.all([
                loadAdminUsers(),
                loadAdminLinks(),
                loadAdminConversions(),
                loadAdminWithdrawals()
            ]);
        } catch (e) {
            console.error('Error loading admin dashboard data:', e);
        }
    }

    async function loadAdminUsers() {
        try {
            const res = await fetch(`${BASE_URL}/api/admin/users?page=1&limit=50`, { headers: getAdminAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                renderAdminUsers(data.items || []);
                const elMetric = document.getElementById('admin-metric-users');
                if (elMetric) elMetric.textContent = data.total || (data.items ? data.items.length : 0);
            }
        } catch (e) { console.error('Admin users fetch error:', e); }
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
                <td><span class="badge approved">Active Account</span></td>
            </tr>
        `).join('');
    }

    async function loadAdminLinks() {
        try {
            const res = await fetch(`${BASE_URL}/api/admin/links?page=1&limit=50`, { headers: getAdminAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                renderAdminLinks(data.items || []);
                const elMetric = document.getElementById('admin-metric-links');
                if (elMetric) {
                    const totalClicks = (data.items || []).reduce((acc, l) => acc + (l.clicks || 0), 0);
                    elMetric.textContent = `${data.total || data.items.length} links (${totalClicks} clicks)`;
                }
            }
        } catch (e) { console.error('Admin links fetch error:', e); }
    }

    function renderAdminLinks(links) {
        const body = document.getElementById('admin-links-body');
        if (!body) return;
        if (links.length === 0) {
            body.innerHTML = '<tr><td colspan="8" class="empty-msg">No generated links recorded.</td></tr>';
            return;
        }

        body.innerHTML = links.map(l => `
            <tr>
                <td>#${l.id}</td>
                <td><strong>${escapeHtml(l.user_name || 'User #' + l.user_id)}</strong></td>
                <td><code>${escapeHtml(l.tracking_id)}</code></td>
                <td>${escapeHtml(l.aff_sub2 || '-')}</td>
                <td>${escapeHtml(l.aff_sub3 || 'shopback')}</td>
                <td><span class="badge approved">${l.clicks || 0} clicks</span></td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(l.original_url)}">${escapeHtml(l.original_url)}</td>
                <td>${formatLocalDateTime(l.created_at)}</td>
            </tr>
        `).join('');
    }

    async function loadAdminConversions() {
        try {
            const res = await fetch(`${BASE_URL}/api/admin/conversions?page=1&limit=50`, { headers: getAdminAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                const items = data.items || [];
                renderAdminConversions(items);

                let totalComm = 0;
                let totalProfit = 0;

                items.forEach(c => {
                    totalComm += parseFloat(c.commission || 0);
                    totalProfit += parseFloat(c.admin_profit || (c.commission - c.cashback) || 0);
                });

                const elComm = document.getElementById('admin-metric-comm');
                const elProfit = document.getElementById('admin-metric-profit');
                if (elComm) elComm.textContent = `₱${totalComm.toFixed(2)}`;
                if (elProfit) elProfit.textContent = `₱${totalProfit.toFixed(2)}`;
            }
        } catch (e) { console.error('Admin conversions fetch error:', e); }
    }

    function renderAdminConversions(conversions) {
        const body = document.getElementById('admin-conversions-body');
        if (!body) return;
        if (conversions.length === 0) {
            body.innerHTML = '<tr><td colspan="9" class="empty-msg">No conversions recorded yet.</td></tr>';
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
                <td><span class="badge ${escapeHtml(c.status)}">${escapeHtml(c.status)}</span></td>
                <td>${formatLocalDateTime(c.created_at)}</td>
            </tr>
        `).join('');
    }

    async function loadAdminWithdrawals() {
        try {
            const res = await fetch(`${BASE_URL}/api/admin/withdrawals`, { headers: getAdminAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                renderAdminWithdrawals(data.items || []);
            }
        } catch (e) { console.error('Admin withdrawals fetch error:', e); }
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
                <td><strong class="tabular-nums" style="color: var(--color-success-text);">₱${parseFloat(w.amount).toFixed(2)}</strong></td>
                <td><code>${escapeHtml(w.account_details)}</code></td>
                <td><span class="badge pending">${w.status}</span></td>
                <td>
                    <button class="action-btn approve-w-btn" data-id="${w.id}" style="padding: 0.35rem 0.65rem; font-size: 0.78rem; background: var(--color-success); border: none; height: auto;">
                        ✅ Approve & Pay Out
                    </button>
                    <button class="nav-btn alt-btn reject-w-btn" data-id="${w.id}" style="padding: 0.35rem 0.65rem; font-size: 0.78rem; border-color: var(--color-danger-text); color: var(--color-danger-text); height: auto;">
                        ❌ Reject
                    </button>
                </td>
            </tr>
        `).join('');

        body.querySelectorAll('.approve-w-btn').forEach(btn => {
            btn.addEventListener('click', () => handleWithdrawalAction(btn.getAttribute('data-id'), 'approve'));
        });

        body.querySelectorAll('.reject-w-btn').forEach(btn => {
            btn.addEventListener('click', () => handleWithdrawalAction(btn.getAttribute('data-id'), 'reject'));
        });
    }

    async function handleWithdrawalAction(withdrawalId, action) {
        try {
            const res = await fetch(`${BASE_URL}/api/admin/withdrawals/${withdrawalId}/${action}`, {
                method: 'POST',
                headers: getAdminAuthHeaders()
            });

            if (res.ok) {
                showToast(`Withdrawal request #${withdrawalId} ${action}d successfully`, 'success');
                await loadAdminData();
            } else {
                showToast(`Failed to ${action} withdrawal request`, 'error');
            }
        } catch (e) {
            console.error('Withdrawal action error:', e);
            showToast('Server connection error', 'error');
        }
    }

    // Admin Webhook Simulation Form
    const adminTestConvForm = document.getElementById('admin-test-conv-form');
    if (adminTestConvForm) {
        adminTestConvForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tracking_id = document.getElementById('adm-sim-tracking-id').value.trim();
            const merchant = document.getElementById('adm-sim-merchant').value.trim();
            const commission = parseFloat(document.getElementById('adm-sim-commission').value);
            const statusVal = document.getElementById('adm-sim-status').value;

            try {
                const res = await fetch(`${BASE_URL}/api/callback/conversion`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        conversion_id: 'conv_adm_' + Date.now(),
                        order_id: 'ord_adm_' + Date.now(),
                        aff_sub1: tracking_id,
                        merchant: merchant,
                        commission: commission,
                        cashback: commission * 0.10,
                        status: statusVal
                    })
                });

                if (res.ok) {
                    showToast(`Test conversion callback processed successfully (${statusVal})!`, 'success');
                    adminTestConvForm.reset();
                    await loadAdminData();
                } else {
                    const errData = await res.json();
                    showToast(`Webhook simulation failed: ${errData.message || errData.detail || 'Unknown error'}`, 'error');
                }
            } catch (err) {
                console.error('Webhook simulation error:', err);
                showToast('Webhook simulation error', 'error');
            }
        });
    }

    // Initialize check
    checkAdminAuth();
});
