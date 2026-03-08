/**
 * CarrierIQ — Shared UI Utilities
 * Toast notifications, spinner, formatters, table helpers
 */

// ─── Toast ────────────────────────────────────────────────────
function toast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerHTML = `<span style="font-size:1.1rem">${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(100%)'; t.style.transition = '0.3s'; setTimeout(() => t.remove(), 300); }, duration);
}

// ─── Spinner ──────────────────────────────────────────────────
function showSpinner(msg = 'AI is processing...') {
    let o = document.getElementById('spinner-overlay');
    if (!o) {
        o = document.createElement('div');
        o.id = 'spinner-overlay';
        o.className = 'spinner-overlay';
        o.innerHTML = `<div class="spinner"></div><div class="spinner-text" id="spinner-msg">${msg}</div>`;
        document.body.appendChild(o);
    }
    o.style.display = 'flex';
    document.getElementById('spinner-msg').textContent = msg;
}

function hideSpinner() {
    const o = document.getElementById('spinner-overlay');
    if (o) o.style.display = 'none';
}

// ─── Formatters ───────────────────────────────────────────────
function formatINR(n) {
    if (!n && n !== 0) return '—';
    return '₹' + Number(n).toLocaleString('en-IN');
}

function formatPct(n) {
    if (!n && n !== 0) return '—';
    return Number(n).toFixed(1) + '%';
}

function formatScore(n) {
    const s = Number(n).toFixed(1);
    const cls = n >= 80 ? 'success' : n >= 60 ? 'warning' : 'danger';
    return `<span class="badge badge-${cls}">${s}</span>`;
}

function getRiskBadge(level) {
    if (!level) return '';
    const lvl = level.toUpperCase();
    const cls = lvl === 'LOW' ? 'risk-badge-low' : lvl === 'MEDIUM' ? 'risk-badge-medium' : 'risk-badge-high';
    const icon = lvl === 'LOW' ? '✅' : lvl === 'MEDIUM' ? '⚠️' : '🚨';
    return `<span class="${cls}">${icon} ${lvl}</span>`;
}

function scoreFill(score) {
    const cls = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
    return `<div class="score-bar-wrap">
    <div class="score-bar-track"><div class="score-bar-fill ${cls}" style="width:${Math.min(score, 100)}%"></div></div>
    <span style="font-size:0.8125rem;font-weight:600;color:var(--text-primary);min-width:38px">${Number(score).toFixed(0)}</span>
  </div>`;
}

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// ─── Auth Guard ───────────────────────────────────────────────
function requireAuth() {
    if (!api.isLoggedIn()) {
        window.location.href = '../pages/auth.html';
        return false;
    }
    return true;
}

function populateUserInfo() {
    const u = api.user;
    if (!u) return;
    const nameEl = document.getElementById('user-name');
    const compEl = document.getElementById('user-company');
    const avatarEl = document.getElementById('user-avatar');
    if (nameEl) nameEl.textContent = u.name;
    if (compEl) compEl.textContent = u.company;
    if (avatarEl) avatarEl.textContent = u.name.charAt(0).toUpperCase();
    // topbar user info
    const tbName = document.getElementById('topbar-user');
    if (tbName) tbName.textContent = u.name;
    const tbComp = document.getElementById('topbar-company');
    if (tbComp) tbComp.textContent = u.company;
}

// ─── Animated Counter ─────────────────────────────────────────
function animateCounter(el, target, suffix = '', duration = 1500) {
    const start = 0;
    const startTime = performance.now();
    const update = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3); // ease out cubic
        const current = Math.round(start + (target - start) * ease);
        el.textContent = current.toLocaleString('en-IN') + suffix;
        if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
}

// ─── Sortable Table ───────────────────────────────────────────
function makeTableSortable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(th => {
        th.style.cursor = 'pointer';
        th.innerHTML += ' <span style="opacity:0.4">↕</span>';
        th.addEventListener('click', () => {
            const col = th.dataset.sort;
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.rows);
            const dir = th.dataset.dir === 'asc' ? -1 : 1;
            th.dataset.dir = dir === 1 ? 'asc' : 'desc';
            rows.sort((a, b) => {
                const av = a.cells[th.cellIndex]?.textContent || '';
                const bv = b.cells[th.cellIndex]?.textContent || '';
                const an = parseFloat(av.replace(/[^0-9.]/g, ''));
                const bn = parseFloat(bv.replace(/[^0-9.]/g, ''));
                if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir;
                return av.localeCompare(bv) * dir;
            });
            rows.forEach(r => tbody.appendChild(r));
        });
    });
}

// ─── Table Search ─────────────────────────────────────────────
function setupTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;
    input.addEventListener('input', () => {
        const q = input.value.toLowerCase();
        Array.from(table.querySelectorAll('tbody tr')).forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
}

// ─── Navigation active ────────────────────────────────────────
function setActiveNav(pageId) {
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.page === pageId);
    });
}

// ─── Markdown-lite renderer (for AI responses) ────────────────
function renderMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^• (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>(\n|$))+/g, '<ul>$&</ul>')
        .replace(/^#{1,3} (.+)$/gm, '<h4 style="margin:12px 0 6px;color:var(--navy)">$1</h4>')
        .replace(/\n/g, '<br>');
}

// ─── Copy to Clipboard ────────────────────────────────────────
function copyText(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = orig, 2000);
        toast('Copied to clipboard', 'success', 2000);
    });
}

// ─── Download text as file ────────────────────────────────────
function downloadText(content, filename) {
    const blob = new Blob([content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
}
