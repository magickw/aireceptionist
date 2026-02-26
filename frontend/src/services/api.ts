import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Auto-detect backend URL based on environment
export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ||
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `${window.location.protocol}//${window.location.hostname}`);

// Extend config type to include retry count
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  __retryCount?: number;
}

// Configure axios with longer timeout and retry logic
const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  timeout: 30000, // 30 second timeout for cold starts
  timeoutErrorMessage: 'Server is starting up. Please try again...',
});

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 2000; // 2 seconds between retries

// Add retry interceptor for network errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as ExtendedAxiosRequestConfig | undefined;

    // Only retry on network errors, not on 401/403
    if (!config) return Promise.reject(error);

    const isNetworkError = !error.response && (
      error.code === 'ECONNABORTED' ||
      error.message.includes('Network Error') ||
      error.message.includes('timeout')
    );

    // Don't retry auth errors
    if (error.response?.status === 401 || error.response?.status === 403) {
      return Promise.reject(error);
    }

    // Retry logic for network errors
    if (isNetworkError && !config.__retryCount) {
      config.__retryCount = 0;
    }

    if (isNetworkError && config.__retryCount !== undefined && config.__retryCount < MAX_RETRIES) {
      config.__retryCount += 1;
      const delay = RETRY_DELAY * config.__retryCount; // Exponential backoff

      console.log(`Retrying request (${config.__retryCount}/${MAX_RETRIES}) after ${delay}ms...`);

      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(api(config));
        }, delay);
      });
    }

    return Promise.reject(error);
  }
);

if (typeof window !== 'undefined') {
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Handle 401 responses - attempt refresh before redirecting to login
  let isRefreshing = false;
  let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = [];

  const processQueue = (error: unknown, token: string | null = null) => {
    failedQueue.forEach(({ resolve, reject }) => {
      if (token) resolve(token);
      else reject(error);
    });
    failedQueue = [];
  };

  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        const refreshToken = localStorage.getItem('refreshToken');

        if (!refreshToken) {
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(error);
        }

        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          }).then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const { data } = await axios.post(`${BACKEND_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('refreshToken', data.refresh_token);
          }
          api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
          processQueue(null, data.access_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      if (error.response?.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }

      return Promise.reject(error);
    }
  );
}

export const getWebSocketUrl = () => {
  const wsProtocol = BACKEND_URL.startsWith('https') ? 'wss' : 'ws';
  const wsBaseUrl = BACKEND_URL.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${wsBaseUrl}/api/voice/ws`;
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

// Forecasting API
export const forecastingApi = {
  getHistory: (days: number = 30) => api.get(`/forecasting/history?days=${days}`),
  getPredictions: (daysAhead: number = 7) => api.get(`/forecasting/predict?days_ahead=${daysAhead}`),
  getWeekly: () => api.get('/forecasting/weekly'),
  getPeakHours: () => api.get('/forecasting/peak-hours'),
};

// Email API
export const emailApi = {
  getStatus: () => api.get('/email/status'),
  send: (data: { to_email: string; subject: string; body: string; html?: boolean }) => api.post('/email/send', data),
  sendCallNotification: (data: { to_email: string; customer_name: string; phone_number: string; call_summary: string }) =>
    api.post('/email/call-notification', data),
  sendAppointmentReminder: (data: { to_email: string; customer_name: string; appointment_time: string; business_name: string }) =>
    api.post('/email/appointment-reminder', data),
};

// Chatbot API
export const chatbotApi = {
  start: (data: { customer_name?: string; customer_email?: string; customer_phone?: string }) => api.post('/chatbot/start', data),
  sendMessage: (data: { session_id: number; message: string }) => api.post('/chatbot/message', data),
  endSession: (sessionId: number) => api.post(`/chatbot/end/${sessionId}`),
  getHistory: (limit: number = 50) => api.get(`/chatbot/history?limit=${limit}`),
};

// Reports API
export const reportsApi = {
  getMetrics: (startDate?: string, endDate?: string) => api.get('/reports/metrics', { params: { start_date: startDate, end_date: endDate } }),
  getCustomerMetrics: (startDate?: string, endDate?: string) => api.get('/reports/customers', { params: { start_date: startDate, end_date: endDate } }),
  getHourlyDistribution: (startDate?: string, endDate?: string) => api.get('/reports/hourly', { params: { start_date: startDate, end_date: endDate } }),
  getWeeklySummary: (weeks: number = 4) => api.get(`/reports/weekly?weeks=${weeks}`),
  generateReport: (reportType: string, startDate?: string, endDate?: string) =>
    api.get('/reports/generate', { params: { report_type: reportType, start_date: startDate, end_date: endDate } }),
  exportCSV: (startDate?: string, endDate?: string) => api.get('/reports/export', { params: { start_date: startDate, end_date: endDate } }),
};

// Sentiment API
export const sentimentApi = {
  analyze: (text: string) => api.post('/sentiment/analyze', { text }),
  analyzeCall: (callId: number) => api.post(`/sentiment/analyze-call/${callId}`),
  getBusiness: (days: number = 30) => api.get(`/sentiment/business?days=${days}`),
  analyzeRealtime: (text: string) => api.post('/sentiment/realtime', { text }),
};

// Churn API
export const churnApi = {
  calculate: (customerPhone: string) => api.post('/churn/calculate', { customer_phone: customerPhone }),
  getAtRisk: (minScore: number = 40) => api.get(`/churn/at-risk?min_score=${minScore}`),
  getStats: () => api.get('/churn/stats'),
};

// Voice Greetings API
export const voiceGreetingsApi = {
  getTypes: () => api.get('/voice-greetings/types'),
  list: () => api.get('/voice-greetings'),
  create: (data: { name: string; greeting_type: string; text: string; language?: string }) => api.post('/voice-greetings', data),
  update: (greetingType: string, data: { is_active?: boolean; text?: string }) => api.put(`/voice-greetings/${greetingType}`, data),
  delete: (greetingType: string) => api.delete(`/voice-greetings/${greetingType}`),
  getPreview: (greetingType: string) => api.get(`/voice-greetings/preview/${greetingType}`),
};

// Call Routing API
export const callRoutingApi = {
  getOptions: () => api.get('/call-routing/options'),
  list: () => api.get('/call-routing'),
  create: (data: { name: string; conditions: any; action: string; action_value: string; priority?: number }) => api.post('/call-routing', data),
  update: (ruleId: number, data: { is_active?: boolean; priority?: number }) => api.put(`/call-routing/${ruleId}`, data),
  delete: (ruleId: number) => api.delete(`/call-routing/${ruleId}`),
  evaluate: (callContext: any) => api.post('/call-routing/evaluate', callContext),
};

// AI Training API
export const aiTrainingApi = {
  getCategories: () => api.get('/ai-training/categories'),
  list: (params?: { category?: string; is_active?: boolean }) => api.get('/ai-training/', { params }),
  get: (id: number) => api.get(`/ai-training/${id}`),
  create: (data: { title: string; user_input: string; expected_response: string; description?: string; category?: string }) =>
    api.post('/ai-training', data),
  update: (id: number, data: { title?: string; user_input?: string; expected_response?: string; description?: string; category?: string; is_active?: boolean }) =>
    api.put(`/ai-training/${id}`, data),
  delete: (id: number) => api.delete(`/ai-training/${id}`),
  test: (id: number) => api.post(`/ai-training/test/${id}`),
  testAll: () => api.post('/ai-training/test-all'),
  getStats: () => api.get('/ai-training/statistics'),
};

// Menu/Pricing API
export const menuApi = {
  list: (businessId: number, params?: { category?: string; available_only?: boolean }) =>
    api.get('/menu/', { params: { business_id: businessId, ...params } }),
  get: (itemId: number, businessId: number) =>
    api.get(`/menu/${itemId}`, { params: { business_id: businessId } }),
  create: (businessId: number, data: { name: string; description?: string; price?: number; unit?: string; category?: string; available?: boolean }) =>
    api.post('/menu/', data, { params: { business_id: businessId } }),
  update: (itemId: number, businessId: number, data: { name?: string; description?: string; price?: number; unit?: string; category?: string; available?: boolean; is_active?: boolean }) =>
    api.put(`/menu/${itemId}`, data, { params: { business_id: businessId } }),
  delete: (itemId: number, businessId: number) =>
    api.delete(`/menu/${itemId}`, { params: { business_id: businessId } }),
  getCategories: (businessId: number) =>
    api.get('/menu/categories/list', { params: { business_id: businessId } }),
};

export default api;
