const API_BASE = typeof window !== 'undefined' && window.__API_BASE__
  ? window.__API_BASE__
  : '/api';

export default API_BASE;