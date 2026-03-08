/**
 * CarrierIQ — Sidebar Component
 * Inject into every dashboard page
 */
function buildSidebar(activePageId) {
    const navItems = [
        { id: 'dashboard', icon: '🏠', label: 'Dashboard', href: 'dashboard.html' },
        { id: 'divider1', type: 'divider', label: 'AI MODULES' },
        { id: 'bid-scoring', icon: '📊', label: 'Bid Upload & Scoring', href: 'bid-scoring.html' },
        { id: 'carrier-dna', icon: '🧬', label: 'Carrier DNA Profiles', href: 'carrier-dna.html' },
        { id: 'risk', icon: '🌡️', label: 'Risk & Intelligence', href: 'risk.html' },
        { id: 'chat', icon: '💬', label: 'Procurement Chat', href: 'chat.html' },
        { id: 'divider2', type: 'divider', label: 'FINANCIALS & DOCS' },
        { id: 'invoice', icon: '🧾', label: 'Invoice Reconciliation AI', href: 'invoice.html' },
        { id: 'rfq', icon: '📝', label: 'Smart RFQ Generator', href: 'rfq.html' },
        { id: 'award', icon: '🏆', label: 'Award Letter', href: 'award.html' },
        { id: 'divider3', type: 'divider', label: 'ANALYTICS & ESG' },
        { id: 'green', icon: '🌱', label: 'Green Freight Tracking', href: 'green.html' },
        { id: 'forecast', icon: '🔮', label: 'Predictive Rate Forecasting', href: 'forecast.html' },
        { id: 'scorecard', icon: '📈', label: 'Performance Scorecard', href: 'scorecard.html' },
        { id: 'benchmark', icon: '💰', label: 'Market Benchmark', href: 'benchmark.html' },
        { id: 'roi', icon: '📉', label: 'Procurement ROI', href: 'roi.html' },
        { id: 'onboard', icon: '🆕', label: 'Carrier Onboarding', href: 'onboard.html' },
    ];

    let html = `
  <div class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-mark">C<span style="font-size:0.65em">IQ</span></div>
      <div>
        <div class="logo-text">CarrierIQ <span class="logo-badge">AI</span></div>
      </div>
    </div>
    <nav class="sidebar-nav">`;

    navItems.forEach(item => {
        if (item.type === 'divider') {
            html += `<div class="nav-section-title" style="margin-top:16px">${item.label}</div>`;
        } else {
            const active = item.id === activePageId ? ' active' : '';
            html += `<a class="nav-item${active}" href="${item.href}" data-page="${item.id}">
        <span class="nav-icon">${item.icon}</span>
        <span>${item.label}</span>
      </a>`;
        }
    });

    html += `</nav>
    <div class="sidebar-footer">
      <div class="user-chip">
        <div class="user-avatar" id="user-avatar">U</div>
        <div>
          <div class="user-name" id="user-name">Loading...</div>
          <div class="user-company" id="user-company">—</div>
        </div>
      </div>
      <a class="nav-item" style="margin-top:8px;cursor:pointer" onclick="api.logout()">
        <span class="nav-icon">🚪</span><span>Sign Out</span>
      </a>
    </div>
  </div>`;

    // Inject topbar
    const topbarHtml = `
  <div class="topbar">
    <div>
      <div class="topbar-title" id="page-title">CarrierIQ</div>
    </div>
    <div class="topbar-right">
      <span style="font-size:0.8125rem;color:var(--text-secondary)" id="topbar-company"></span>
      <div style="width:1px;height:20px;background:var(--border)"></div>
      <span style="font-size:0.875rem;font-weight:600;color:var(--text-primary)" id="topbar-user"></span>
      <div class="user-avatar" style="width:34px;height:34px;font-size:0.8125rem" id="topbar-avatar">U</div>
    </div>
  </div>`;

    return { sidebarHtml: html, topbarHtml };
}

function injectLayout(pageId, pageTitle) {
    if (!requireAuth()) return false;

    const { sidebarHtml, topbarHtml } = buildSidebar(pageId);

    // Create main app wrapper if not exists
    let layout = document.getElementById('app-layout');
    if (!layout) {
        layout = document.createElement('div');
        layout.className = 'app-layout';
        layout.id = 'app-layout';
        document.body.prepend(layout);
    }

    // Inject sidebar if not exists
    let sidebar = layout.querySelector('.sidebar');
    if (!sidebar) {
        const temp = document.createElement('div');
        temp.innerHTML = sidebarHtml;
        sidebar = temp.firstElementChild;
        layout.prepend(sidebar);
    } else {
        sidebar.outerHTML = sidebarHtml;
    }

    // 1. Ensure only one main-content exists and it's inside layout
    let mainEl = document.querySelector('.main-content');
    if (!mainEl) {
        mainEl = document.createElement('div');
        mainEl.className = 'main-content';
    }
    
    // Ensure it's inside the layout
    if (mainEl.parentElement !== layout) {
        layout.appendChild(mainEl);
    }

    // 2. Remove any other duplicate main-contents
    document.querySelectorAll('.main-content').forEach(el => {
        if (el !== mainEl) el.remove();
    });

    // 3. Inject Topbar if not exists
    let topbar = mainEl.querySelector('.topbar');
    if (!topbar) {
        const topbarWrap = document.createElement('div');
        topbarWrap.innerHTML = topbarHtml;
        mainEl.prepend(topbarWrap.firstElementChild);
    } else {
        topbar.outerHTML = topbarHtml;
    }

    // 4. Move page-content into mainEl
    const pageContent = document.getElementById('page-content');
    if (pageContent && pageContent.parentElement !== mainEl) {
        mainEl.appendChild(pageContent);
    }

    // Set page title
    const ptEl = document.getElementById('page-title');
    if (ptEl) ptEl.textContent = pageTitle;

    // Populate user info
    populateUserInfo();
    // Also set topbar avatar
    setTimeout(() => {
        const av = document.getElementById('topbar-avatar');
        if (av && api.user) av.textContent = api.user.name.charAt(0).toUpperCase();
    }, 100);

    return true;
}
