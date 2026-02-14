import axios from 'axios';

export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://receptium.onrender.com';
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'wss://receptium.onrender.com';

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
});

if (typeof window !== 'undefined') {
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
}

export const getWebSocketUrl = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return `${WS_URL}/api/voice/ws${token ? `?token=${token}` : ''}`;
};

export default api;
