/**
 * API Utilities - Authentication wrapper and fetch helpers
 * @module utils/api
 */

/**
 * Get current auth token from session storage
 * @returns {string|null}
 */
export function getToken() {
    return sessionStorage.getItem('access_token');
}

/**
 * Check if current user is admin
 * @returns {boolean}
 */
export function isAdmin() {
    return sessionStorage.getItem('is_admin') === 'true';
}

/**
 * Authenticated fetch wrapper - adds Authorization header and handles 401
 * @param {string} url - The URL to fetch
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function authFetch(url, options = {}) {
    const token = getToken();
    const headers = options.headers || {};
    headers['Authorization'] = `Bearer ${token}`;
    options.headers = headers;

    const response = await fetch(url, options);
    if (response.status === 401) {
        logout();
    }
    return response;
}

/**
 * Logout user - clear session and redirect
 */
export function logout() {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('is_admin');
    window.location.href = '/login';
}

/**
 * Check authentication and redirect if not authenticated
 * @returns {boolean} - true if authenticated
 */
export function requireAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Expose globally for compatibility with existing code
window.authFetch = authFetch;
window.logout = logout;
