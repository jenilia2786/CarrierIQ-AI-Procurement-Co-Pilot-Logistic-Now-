/**
 * CarrierIQ — API Client
 * All backend communication in one place
 */

const API_BASE = 'http://localhost:8000';

class APIClient {
    constructor() {
        this.token = localStorage.getItem('carrieriq_token');
        this.user = JSON.parse(localStorage.getItem('carrieriq_user') || 'null');
    }

    _headers(extra = {}) {
        const h = { 'Content-Type': 'application/json', ...extra };
        if (this.token) h['Authorization'] = `Bearer ${this.token}`;
        return h;
    }

    async _req(method, path, body = null, isFormData = false) {
        const opts = {
            method,
            headers: isFormData ? (this.token ? { Authorization: `Bearer ${this.token}` } : {}) : this._headers(),
        };
        if (body) opts.body = isFormData ? body : JSON.stringify(body);

        try {
            const resp = await fetch(`${API_BASE}${path}`, opts);
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(err.detail || `HTTP ${resp.status}`);
            }
            return await resp.json();
        } catch (e) {
            if (e.name === 'TypeError' && e.message.includes('fetch')) {
                throw new Error('Cannot connect to backend. Is the server running on port 8000?');
            }
            throw e;
        }
    }

    // ─── Auth ────────────────────────────────────────────────────
    async signup(name, company, email, password) {
        const data = await this._req('POST', '/auth/signup', { name, company, email, password });
        this._saveAuth(data);
        return data;
    }

    async login(email, password) {
        const data = await this._req('POST', '/auth/login', { email, password });
        this._saveAuth(data);
        return data;
    }

    _saveAuth(data) {
        this.token = data.access_token;
        this.user = data.user;
        localStorage.setItem('carrieriq_token', data.access_token);
        localStorage.setItem('carrieriq_user', JSON.stringify(data.user));
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('carrieriq_token');
        localStorage.removeItem('carrieriq_user');
        window.location.href = '/';
    }

    isLoggedIn() { return !!this.token && !!this.user; }

    // ─── Dashboard ───────────────────────────────────────────────
    async getDashboardStats() {
        const uid = this.user?.id || 'demo';
        return await this._req('GET', `/dashboard/stats?user_id=${uid}`);
    }

    // ─── Carriers ────────────────────────────────────────────────
    async getAllCarriers() {
        return await this._req('GET', '/carriers/all');
    }

    async getCarrier(id) {
        return await this._req('GET', `/carriers/${id}`);
    }

    async getBackupCarrier(id, lane = '') {
        return await this._req('GET', `/carriers/${id}/backup?lane=${encodeURIComponent(lane)}`);
    }

    async uploadBids(formData) {
        return await this._req('POST', '/carriers/upload-bids', formData, true);
    }

    async uploadBidsJSON(bids) {
        const fd = new FormData();
        fd.append('bids_json', JSON.stringify(bids));
        fd.append('user_id', this.user?.id || 'demo');
        return await this._req('POST', '/carriers/upload-bids', fd, true);
    }

    // ─── Chat ────────────────────────────────────────────────────
    async chat(query) {
        return await this._req('POST', '/chat', { query, user_id: this.user?.id || 'demo' });
    }

    async getChatHistory() {
        const uid = this.user?.id || 'demo';
        return await this._req('GET', `/chat/history/${uid}`);
    }

    // ─── Documents ───────────────────────────────────────────────
    async generateRFQ(params) {
        return await this._req('POST', '/rfq/generate', { ...params, user_id: this.user?.id || 'demo' });
    }

    async generateAwardLetter(params) {
        return await this._req('POST', '/award/generate', { ...params, user_id: this.user?.id || 'demo' });
    }

    // ─── Analytics ───────────────────────────────────────────────
    async updateScorecard(params) {
        return await this._req('POST', '/scorecard/update', { ...params, user_id: this.user?.id || 'demo' });
    }

    async getBenchmarks() {
        return await this._req('GET', '/benchmark/lanes');
    }

    async getROI() {
        const uid = this.user?.id || 'demo';
        return await this._req('GET', `/roi/summary?user_id=${uid}`);
    }

    async scoreNewCarrier(params) {
        return await this._req('POST', '/onboard/score', params);
    }
}

const api = new APIClient();
