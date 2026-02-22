/**
 * Voice-related TypeScript types for the AI Receptionist frontend.
 */

export interface CallSession {
  id: string;
  business_id: number;
  customer_phone?: string;
  call_type: string;
  created_at: string;
  status: 'active' | 'ended';
}

export interface Message {
  role: 'customer' | 'ai';
  content: string;
  timestamp?: string;
}

export interface ReasoningData {
  intent?: string;
  confidence?: number;
  selected_action?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  escalation_risk?: number;
  entities?: Record<string, unknown>;
  suggested_response?: string;
  reasoning_chain?: ReasoningStep[];
}

export interface ReasoningStep {
  step?: string;
  message?: string;
  data?: Record<string, unknown>;
}

export interface LatencyMetrics {
  time_to_first_chunk_ms?: number;
  total_latency_ms?: number;
}

export interface VoiceState {
  isRecording: boolean;
  isPlaying: boolean;
  isProcessing: boolean;
  isConnected: boolean;
  error?: string;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

export interface AudioConfig {
  sample_rate: number;
  channels: number;
  bit_depth: number;
  format: string;
}

export interface OrderItem {
  name: string;
  price: number;
  quantity: number;
  menu_item_id?: number;
}

export interface AppointmentInfo {
  start_time: string;
  end_time: string;
  service: string;
}
