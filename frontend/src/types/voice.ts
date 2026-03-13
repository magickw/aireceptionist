/**
 * Voice-related TypeScript types for the AI Receptionist frontend.
 */

// ============================================================================
// WebSocket Message Types - Constants and Types
// ============================================================================

/**
 * WebSocket message type constants for voice communication.
 * Used for type-safe message handling between frontend and backend.
 */
export const WS_MESSAGE_TYPES = {
  // Client -> Server messages
  AUDIO_START: 'audio_start',
  AUDIO: 'audio',
  AUDIO_STOP: 'audio_stop',
  USER_INPUT: 'user_input',
  
  // Server -> Client messages
  TEXT_CHUNK: 'text_chunk',
  TRANSCRIPT: 'transcript',
  AUDIO_RESPONSE: 'audio',
  REASONING: 'reasoning',
  TOOL_CALL: 'tool_call',
  TURN_COMPLETE: 'turn_complete',
  ERROR: 'error',
  LATENCY: 'latency',
  SAFETY_TRIGGER: 'safety_trigger',
} as const;

export type WsMessageType = typeof WS_MESSAGE_TYPES[keyof typeof WS_MESSAGE_TYPES];

/** Client-to-server messages */
export interface WsAudioStartMessage {
  type: typeof WS_MESSAGE_TYPES.AUDIO_START;
  sample_rate: number;
}

export interface WsAudioMessage {
  type: typeof WS_MESSAGE_TYPES.AUDIO;
  content: string; // base64 encoded PCM16
}

export interface WsAudioStopMessage {
  type: typeof WS_MESSAGE_TYPES.AUDIO_STOP;
}

export interface WsUserInputMessage {
  type: typeof WS_MESSAGE_TYPES.USER_INPUT;
  text: string;
}

/** Server-to-client messages */
export interface WsTextChunkMessage {
  type: typeof WS_MESSAGE_TYPES.TEXT_CHUNK;
  chunk: string;
}

export interface WsTranscriptMessage {
  type: typeof WS_MESSAGE_TYPES.TRANSCRIPT;
  text: string;
  is_partial?: boolean;
}

export interface WsAudioResponseMessage {
  type: typeof WS_MESSAGE_TYPES.AUDIO_RESPONSE;
  audio: string; // base64 encoded PCM16
  sample_rate?: number;
}

export interface WsReasoningMessage {
  type: typeof WS_MESSAGE_TYPES.REASONING;
  reasoning: ReasoningData;
}

export interface WsToolCallMessage {
  type: typeof WS_MESSAGE_TYPES.TOOL_CALL;
  tool_use_id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface WsTurnCompleteMessage {
  type: typeof WS_MESSAGE_TYPES.TURN_COMPLETE;
}

export interface WsErrorMessage {
  type: typeof WS_MESSAGE_TYPES.ERROR;
  message: string;
}

export interface WsLatencyMessage {
  type: typeof WS_MESSAGE_TYPES.LATENCY;
  metrics: LatencyMetrics;
}

export interface WsSafetyTriggerMessage {
  type: typeof WS_MESSAGE_TYPES.SAFETY_TRIGGER;
  reason: string;
  should_escalate: boolean;
}

/** Union type for all WebSocket messages */
export type WebSocketClientMessage =
  | WsAudioStartMessage
  | WsAudioMessage
  | WsAudioStopMessage
  | WsUserInputMessage;

export type WebSocketServerMessage =
  | WsTextChunkMessage
  | WsTranscriptMessage
  | WsAudioResponseMessage
  | WsReasoningMessage
  | WsToolCallMessage
  | WsTurnCompleteMessage
  | WsErrorMessage
  | WsLatencyMessage
  | WsSafetyTriggerMessage;

// ============================================================================
// Browser Compatibility
// ============================================================================

/**
 * Browser compatibility information for voice features.
 */
export interface BrowserCompatibility {
  supported: boolean;
  audioContext: boolean;
  getUserMedia: boolean;
  webSocket: boolean;
  mediaRecorder: boolean;
  browserName: string;
  browserVersion: string;
  warnings: string[];
}

/**
 * Detect browser compatibility for voice features.
 * @returns Compatibility information object
 */
export function detectBrowserCompatibility(): BrowserCompatibility {
  const warnings: string[] = [];
  
  // Detect browser
  const ua = navigator.userAgent;
  let browserName = 'Unknown';
  let browserVersion = '';
  
  if (ua.includes('Firefox/')) {
    browserName = 'Firefox';
    browserVersion = ua.match(/Firefox\/(\d+)/)?.[1] || '';
  } else if (ua.includes('Edg/')) {
    browserName = 'Edge';
    browserVersion = ua.match(/Edg\/(\d+)/)?.[1] || '';
  } else if (ua.includes('Chrome/')) {
    browserName = 'Chrome';
    browserVersion = ua.match(/Chrome\/(\d+)/)?.[1] || '';
  } else if (ua.includes('Safari/') && !ua.includes('Chrome')) {
    browserName = 'Safari';
    browserVersion = ua.match(/Version\/(\d+)/)?.[1] || '';
  }
  
  // Check features
  const audioContext = typeof AudioContext !== 'undefined' || 
                       typeof (window as any).webkitAudioContext !== 'undefined';
  const getUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  const webSocket = typeof WebSocket !== 'undefined';
  const mediaRecorder = typeof MediaRecorder !== 'undefined';
  
  // Browser-specific warnings
  if (browserName === 'Safari') {
    warnings.push('Safari may use a different sample rate than requested. Audio resampling is handled automatically.');
  }
  
  if (browserName === 'Firefox' && parseInt(browserVersion) < 115) {
    warnings.push('Older Firefox versions may have audio processing issues. Please update to the latest version.');
  }
  
  if (!audioContext) {
    warnings.push('AudioContext is not supported. Voice features will not work.');
  }
  
  if (!getUserMedia) {
    warnings.push('getUserMedia is not supported. Microphone access will not be available.');
  }
  
  const supported = audioContext && getUserMedia && webSocket;
  
  return {
    supported,
    audioContext,
    getUserMedia,
    webSocket,
    mediaRecorder,
    browserName,
    browserVersion,
    warnings,
  };
}

// ============================================================================
// Core Types
// ============================================================================

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
  stt_latency_ms?: number;
  tts_latency_ms?: number;
  model_latency_ms?: number;
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

/** Default audio configuration for voice streaming */
export const DEFAULT_AUDIO_CONFIG: AudioConfig = {
  sample_rate: 16000,
  channels: 1,
  bit_depth: 16,
  format: 'pcm16',
};

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
