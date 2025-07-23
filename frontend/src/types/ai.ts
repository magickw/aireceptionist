// AI Conversation Engine Types
export interface ConversationMessage {
  id: string;
  timestamp: Date;
  sender: 'customer' | 'ai';
  content: string;
  type: 'text' | 'action' | 'system';
  metadata?: {
    confidence?: number;
    intent?: string;
    entities?: Record<string, any>;
  };
}

export interface CallSession {
  id: string;
  customerPhone: string;
  status: 'active' | 'ended' | 'on-hold';
  startTime: Date;
  endTime?: Date;
  messages: ConversationMessage[];
  context: ConversationContext;
  summary?: CallSummary;
}

export interface ConversationContext {
  customerInfo: {
    name?: string;
    phone?: string;
    email?: string;
  };
  intent: 'booking' | 'ordering' | 'inquiry' | 'complaint' | 'unknown';
  bookingInfo?: {
    service?: string;
    date?: string;
    time?: string;
    duration?: number;
    completed: boolean;
  };
  orderInfo?: {
    items: OrderItem[];
    total?: number;
    completed: boolean;
  };
  businessContext: {
    businessType: string;
    services: Service[];
    operatingHours: Record<string, any>;
    menu?: MenuItem[];
  };
}

export interface OrderItem {
  id: string;
  name: string;
  quantity: number;
  price: number;
  notes?: string;
}

export interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  available: boolean;
}

export interface Service {
  id: string;
  name: string;
  description: string;
  duration: number;
  price: number;
  category: string;
}

export interface CallSummary {
  satisfactionScore: number;
  intent: string;
  resolved: boolean;
  actionsTaken: string[];
  keyTopics: string[];
  sentiment: 'positive' | 'neutral' | 'negative';
  followUpRequired: boolean;
}

export interface AIResponse {
  message: string;
  confidence: number;
  intent: string;
  entities: Record<string, any>;
  actions: AIAction[];
}

export interface AIAction {
  type: 'create_booking' | 'create_order' | 'transfer_call' | 'request_info' | 'provide_info';
  data: Record<string, any>;
  completed: boolean;
}