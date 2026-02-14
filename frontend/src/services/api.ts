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

// Webhooks API
export const webhooksApi = {
  list: () => api.get('/webhooks'),
  getEvents: () => api.get('/webhooks/events'),
  create: (data: { name: string; url: string; events: string[] }) => api.post('/webhooks', data),
  delete: (id: number) => api.delete(`/webhooks/${id}`),
};

// Calendar API
export const calendarApi = {
  list: () => api.get('/calendar'),
  connectGoogle: () => api.get('/calendar/connect/google'),
  connectMicrosoft: () => api.get('/calendar/connect/microsoft'),
  getEvents: (integrationId: number, startDate?: string, endDate?: string) => 
    api.get(`/calendar/${integrationId}/events`, { params: { start_date: startDate, end_date: endDate } }),
  createEvent: (integrationId: number, data: { summary: string; description: string; start_time: string; end_time: string; attendees?: string[] }) =>
    api.post(`/calendar/${integrationId}/events`, data),
  delete: (id: number) => api.delete(`/calendar/${id}`),
};

// SMS API
export const smsApi = {
  listTemplates: () => api.get('/sms/templates'),
  getDefaults: () => api.get('/sms/templates/defaults'),
  createTemplate: (data: { name: string; event_type: string; content: string }) => api.post('/sms/templates', data),
  send: (data: { to_number: string; message: string; media_url?: string }) => api.post('/sms/send', data),
  getStatus: () => api.get('/sms/status'),
};

export default api;
