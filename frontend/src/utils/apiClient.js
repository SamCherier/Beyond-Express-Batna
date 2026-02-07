const API_BASE = process.env.REACT_APP_BACKEND_URL;

function getAuthHeaders() {
  const token = localStorage.getItem('token') || document.cookie.split(';').find(c => c.trim().startsWith('session_token='))?.split('=')?.[1];
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function isRetryable(status) {
  return status === 429 || status >= 500;
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * API call with automatic retry + exponential backoff
 * @param {string} endpoint - API path (e.g. '/api/returns')
 * @param {object} options - fetch options (method, body, etc.)
 * @param {number} retries - number of retry attempts (default 3)
 * @returns {Promise<any>} parsed JSON response
 */
export async function apiCall(endpoint, options = {}, retries = 3) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    ...options,
    headers: { ...getAuthHeaders(), ...options.headers },
    credentials: 'include',
  };

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch(url, { ...config, signal: controller.signal });
      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 401) {
          // Auth failed - redirect to login
          localStorage.removeItem('token');
          window.location.href = '/login';
          throw new Error('Session expired');
        }
        if (attempt < retries && isRetryable(response.status)) {
          await sleep(1000 * Math.pow(2, attempt));
          continue;
        }
        const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        if (attempt < retries) {
          await sleep(1000 * Math.pow(2, attempt));
          continue;
        }
        throw new Error('Request timeout');
      }
      if (attempt >= retries) throw error;
      await sleep(1000 * Math.pow(2, attempt));
    }
  }
}

export default apiCall;
