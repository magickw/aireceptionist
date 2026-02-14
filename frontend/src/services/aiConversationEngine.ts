import { ConversationMessage, ConversationContext, AIResponse, CallSummary } from '@/types/ai';
import OpenRouterService from './openRouterService';

class AIConversationEngine {
  private businessContext: any;
  private openRouterService: OpenRouterService;
  private useAdvancedAI: boolean = true; // Re-enable OpenRouter with better error handling
  private intents: Record<string, RegExp[]> = {
    greeting: [
      /^(hi|hello|hey|good morning|good afternoon|good evening)$/i,
      /^(how are you|howdy)$/i,
    ],
    booking: [
      /book.*appointment/i,
      /schedule.*appointment/i,
      /make.*reservation/i,
      /book.*reservation/i,
      /need.*appointment/i,
      /want.*appointment/i,
      /reserve.*table/i,
      /table.*for/i,
      /reservation.*for/i,
      /book.*table/i,
      /i'd like.*reservation/i,
      /i would like.*reservation/i,
      /i'd like.*table/i,
      /dinner.*tonight/i,
      /lunch.*today/i,
    ],
    ordering: [
      /order/i,
      /buy/i,
      /purchase/i,
      /get.*food/i,
      /delivery/i,
      /takeout/i,
      /place.*order/i,
      /i'd like.*order/i,
    ],
    inquiry: [
      /what.*hours/i,
      /when.*open/i,
      /what.*services/i,
      /how much/i,
      /price/i,
      /cost/i,
      /menu/i,
      /location/i,
      /address/i,
      /where.*located/i,
    ],
    complaint: [
      /problem/i,
      /issue/i,
      /complaint/i,
      /unhappy/i,
      /dissatisfied/i,
      /terrible/i,
      /awful/i,
      /manager/i,
    ],
    farewell: [
      /^(goodbye|bye|thanks|thank you|that's all|have a good day)$/i,
      /^(see you|talk to you later|take care)$/i,
    ],
  };

  private entities = {
    name: /(?:my name is|i'm|i am|this is)\s+([a-zA-Z\s]+)/i,
    phone: /(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})/,
    email: /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/,
    date: /(today|tomorrow|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}\/\d{1,2}|\d{1,2}-\d{1,2})/i,
    time: /(\d{1,2}:\d{2}\s*(am|pm)?|\d{1,2}\s*(am|pm)|noon|morning|afternoon|evening)/i,
    service: /(?:for|book|schedule)\s+(.*?)(?:\s+(?:appointment|service|treatment))/i,
  };

  constructor(businessContext: any) {
    this.businessContext = businessContext;
    this.openRouterService = new OpenRouterService();
  }

  public async processMessage(message: string, context: ConversationContext, conversationHistory?: ConversationMessage[]): Promise<AIResponse> {
    console.log('🔥 AI Engine - Processing message:', message);
    console.log('🔥 AI Engine - Current context:', context);
    console.log('🔥 AI Engine - Conversation history:', conversationHistory);
    
    const intent = this.detectIntent(message);
    const entities = this.extractEntities(message);
    const confidence = this.calculateConfidence(message, intent, entities);

    console.log('🔥 AI Engine - Detected intent:', intent);
    console.log('🔥 AI Engine - Extracted entities:', entities);

    // Update context with extracted entities
    this.updateContext(context, entities, intent);

    // Generate appropriate response
    let response: string;
    
    try {
      if (this.useAdvancedAI) {
        // Use OpenRouter for more natural responses
        console.log('🔥 AI Engine - Using advanced AI for response generation');
        response = await this.openRouterService.generateSmartResponse(
          message, 
          context.businessContext || this.businessContext,
          conversationHistory || [],
          context
        );
        console.log('🔥 AI Engine - OpenRouter response:', response);
      } else {
        console.log('🔥 AI Engine - Using rule-based response generation');
        response = this.generateResponse(message, intent, entities, context);
        console.log('🔥 AI Engine - Rule-based response:', response);
      }
    } catch (error) {
      console.error('🔥 AI Engine - AI response generation error:', error);
      // Fallback to rule-based response
      console.log('🔥 AI Engine - Falling back to rule-based response');
      response = this.generateResponse(message, intent, entities, context);
    }

    const actions = this.determineActions(intent, entities, context);

    console.log('🔥 AI Engine - Final response:', response);
    console.log('🔥 AI Engine - Determined actions:', actions);

    const result = {
      message: response,
      confidence,
      intent,
      entities,
      actions: actions || [], // Ensure actions is always an array
    };

    console.log('🔥 AI Engine - Returning result:', result);
    return result;
  }

  private detectIntent(message: string): string {
    console.log('🔍 Detecting intent for message:', message);
    
    // Priority order: booking > ordering > complaint > inquiry > greeting
    const intentPriority = ['booking', 'ordering', 'complaint', 'inquiry', 'greeting'];
    
    for (const intent of intentPriority) {
      const patterns = this.intents[intent];
      for (const pattern of patterns) {
        if (pattern.test(message)) {
          console.log('🔍 Matched intent:', intent, 'with pattern:', pattern);
          return intent;
        }
      }
    }
    
    console.log('🔍 No intent matched, returning unknown');
    return 'unknown';
  }

  private extractEntities(message: string): Record<string, any> {
    const entities: Record<string, any> = {};

    for (const [entityType, pattern] of Object.entries(this.entities)) {
      const match = message.match(pattern);
      if (match) {
        entities[entityType] = match[1] || match[0];
      }
    }

    return entities;
  }

  private calculateConfidence(message: string, intent: string, entities: Record<string, any>): number {
    let confidence = 0.5; // Base confidence

    // Increase confidence based on intent detection
    if (intent !== 'unknown') confidence += 0.2;

    // Increase confidence based on entities found
    const entityCount = Object.keys(entities).length;
    confidence += Math.min(entityCount * 0.1, 0.3);

    return Math.min(confidence, 1.0);
  }

  private updateContext(context: ConversationContext, entities: Record<string, any>, intent: string): void {
    // Update customer info
    if (entities.name) context.customerInfo.name = entities.name.trim();
    if (entities.phone) context.customerInfo.phone = entities.phone;
    if (entities.email) context.customerInfo.email = entities.email;

    // Update intent if more specific
    if (intent !== 'unknown') context.intent = intent as any;

    // Update booking info
    if (intent === 'booking') {
      if (!context.bookingInfo) {
        context.bookingInfo = { completed: false };
      }
      if (entities.service) context.bookingInfo.service = entities.service;
      if (entities.date) context.bookingInfo.date = entities.date;
      if (entities.time) context.bookingInfo.time = entities.time;
    }

    // Check if booking is complete
    if (context.bookingInfo) {
      context.bookingInfo.completed = !!(
        context.customerInfo.name &&
        context.customerInfo.phone &&
        context.bookingInfo.service &&
        context.bookingInfo.date &&
        context.bookingInfo.time
      );
    }
  }

  private generateResponse(
    message: string,
    intent: string,
    entities: Record<string, any>,
    context: ConversationContext
  ): string {
    const businessType = context.businessContext?.businessType || this.businessContext.type;

    switch (intent) {
      case 'greeting':
        return this.generateGreetingResponse(businessType);
      case 'booking':
        return this.generateBookingResponse(entities, context, businessType);
      case 'ordering':
        return this.generateOrderingResponse(entities, context, businessType);
      case 'inquiry':
        return this.generateInquiryResponse(message, entities, context, businessType);
      case 'complaint':
        return "I understand your concern and I want to help resolve this issue. Let me connect you with a manager who can assist you better.";
      case 'farewell':
        return this.generateFarewellResponse(businessType);
      default:
        return this.generateDefaultResponse(businessType);
    }
  }

  private generateGreetingResponse(businessType: string): string {
    // For stand-alone greetings, provide a welcoming response that encourages continuation
    const businessSpecificGreetings = {
      restaurant: [
        "Hello! Welcome to our restaurant. Are you looking to make a reservation or place an order?",
        "Hi there! Thank you for calling. Would you like to book a table or hear about our menu?",
        "Good day! How can I help you today? Are you interested in dining with us?",
      ],
      salon: [
        "Hello! Welcome to our salon. Are you looking to book an appointment today?",
        "Hi there! Thanks for calling. What service can we schedule for you?",
        "Good day! How can I help you? Are you interested in booking a hair appointment?",
      ],
      medical: [
        "Hello, thank you for calling our medical practice. How may I assist you today?",
        "Hi there! Are you looking to schedule an appointment with one of our doctors?",
        "Good day! How can I help you? Do you need to book a consultation?",
      ],
      default: [
        "Hello! Thank you for calling. How can I help you today?",
        "Hi there! Welcome. What can I do for you?",
        "Good day! How may I assist you?",
      ]
    };

    const greetings = businessSpecificGreetings[businessType] || businessSpecificGreetings.default;
    return greetings[Math.floor(Math.random() * greetings.length)];
  }

  private generateFarewellResponse(businessType: string): string {
    const farewells = [
      "Thank you for calling! Have a wonderful day and we look forward to serving you soon.",
      "It was great talking with you! Thank you for choosing us. Have a great day!",
      "Thank you for your call! We appreciate your business. Have a wonderful day!",
    ];
    return farewells[Math.floor(Math.random() * farewells.length)];
  }

  private generateBookingResponse(entities: Record<string, any>, context: ConversationContext, businessType: string): string {
    const booking = context.bookingInfo;
    const customer = context.customerInfo;

    console.log('Generating booking response - entities:', entities, 'booking:', booking, 'customer:', customer);

    if (booking?.completed) {
      return `Perfect! I have all the information I need. Let me book your ${booking.service} appointment for ${booking.date} at ${booking.time} under the name ${customer.name}. You'll receive a confirmation call at ${customer.phone}. Is there anything else I can help you with?`;
    }

    // Ask for missing information
    if (!customer.name) {
      return "I'd be happy to help you book an appointment! May I start by getting your name?";
    }
    if (!customer.phone) {
      return `Thank you, ${customer.name}! I'll need your phone number for the appointment.`;
    }
    if (!booking?.service) {
      const services = (this.businessContext.services || []).map((s: any) => s.name).join(', ');
      if (services) {
        return `What service would you like to book? We offer: ${services}.`;
      } else {
        return "What type of appointment would you like to schedule?";
      }
    }
    if (!booking?.date) {
      return "What date would work best for your appointment?";
    }
    if (!booking?.time) {
      return "What time would you prefer for your appointment?";
    }

    return "I'd be happy to help you schedule an appointment. Let me gather some information.";
  }

  private generateOrderingResponse(entities: Record<string, any>, context: ConversationContext, businessType: string): string {
    if (businessType !== 'restaurant') {
      return "I'd be happy to help, but we don't currently offer ordering. Would you like to schedule an appointment instead?";
    }

    const order = context.orderInfo;
    const customer = context.customerInfo;

    if (order?.completed) {
      const total = order.total || 0;
      return `Great! I have your order ready. Your total is $${total.toFixed(2)}. We'll have this ready for pickup. Thank you for your order!`;
    }

    if (!customer.name) {
      return "I'd be happy to take your order! May I start by getting your name?";
    }
    if (!customer.phone) {
      return `Thank you, ${customer.name}! I'll need your phone number for the order.`;
    }

    return "What would you like to order today? I can tell you about our menu items if you'd like.";
  }

  private generateInquiryResponse(message: string, entities: Record<string, any>, context: ConversationContext, businessType: string): string {
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('hours') || lowerMessage.includes('open') || lowerMessage.includes('close')) {
      return this.getBusinessHours();
    }

    if (lowerMessage.includes('menu') || lowerMessage.includes('food')) {
      if (businessType === 'restaurant') {
        return "We have a variety of delicious options! Our menu includes appetizers, main courses, and desserts. Would you like me to tell you about any specific category?";
      }
      return "Let me tell you about our services instead. We offer various treatments and consultations.";
    }

    if (lowerMessage.includes('price') || lowerMessage.includes('cost') || lowerMessage.includes('how much')) {
      return "Our pricing varies by service. Would you like me to tell you about pricing for a specific service?";
    }

    if (lowerMessage.includes('services')) {
      const services = this.businessContext.services.map((s: any) => s.name).join(', ');
      return `We offer the following services: ${services}. Would you like more details about any of these?`;
    }

    return "I'd be happy to help answer your question. Could you be more specific about what information you need?";
  }

  private generateDefaultResponse(businessType: string): string {
    return "Thank you for calling! I'm here to help you with appointments, answer questions about our services, or connect you with the right person. How can I assist you today?";
  }

  private getBusinessHours(): string {
    const hours = this.businessContext.operatingHours;
    if (!hours) {
      return "We're open Monday through Friday. Please call during business hours for specific times.";
    }

    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const openDays = [];

    for (let i = 0; i < 7; i++) {
      const dayHours = hours[i];
      if (dayHours && !dayHours.closed) {
        openDays.push(`${daysOfWeek[i]} ${dayHours.open}:00 - ${dayHours.close}:00`);
      }
    }

    return `Our business hours are: ${openDays.join(', ')}.`;
  }

  private determineActions(intent: string, entities: Record<string, any>, context: ConversationContext): any[] {
    const actions = [];

    if (intent === 'booking' && context.bookingInfo?.completed) {
      actions.push({
        type: 'create_booking',
        data: {
          customerName: context.customerInfo.name,
          customerPhone: context.customerInfo.phone,
          service: context.bookingInfo.service,
          date: context.bookingInfo.date,
          time: context.bookingInfo.time,
        },
        completed: false,
      });
    }

    if (intent === 'ordering' && context.orderInfo?.completed) {
      actions.push({
        type: 'create_order',
        data: {
          customerName: context.customerInfo.name,
          customerPhone: context.customerInfo.phone,
          items: context.orderInfo.items,
          total: context.orderInfo.total,
        },
        completed: false,
      });
    }

    if (intent === 'complaint') {
      actions.push({
        type: 'transfer_call',
        data: { reason: 'complaint', priority: 'high' },
        completed: false,
      });
    }

    return actions;
  }

  public generateCallSummary(messages: ConversationMessage[], context: ConversationContext): CallSummary {
    const actionsTaken = [];
    let resolved = false;

    if (context.bookingInfo?.completed) {
      actionsTaken.push('Appointment booked');
      resolved = true;
    }

    if (context.orderInfo?.completed) {
      actionsTaken.push('Order placed');
      resolved = true;
    }

    // Analyze sentiment based on message content
    const customerMessages = messages.filter(m => m.sender === 'customer');
    const sentiment = this.analyzeSentiment(customerMessages);

    // Calculate satisfaction score
    const satisfactionScore = this.calculateSatisfactionScore(sentiment, resolved, context.intent);

    // Extract key topics
    const keyTopics = this.extractKeyTopics(messages);

    return {
      satisfactionScore,
      intent: context.intent,
      resolved,
      actionsTaken,
      keyTopics,
      sentiment,
      followUpRequired: !resolved && context.intent !== 'inquiry',
    };
  }

  private analyzeSentiment(messages: ConversationMessage[]): 'positive' | 'neutral' | 'negative' {
    const positiveWords = ['thank', 'great', 'good', 'excellent', 'perfect', 'wonderful', 'amazing'];
    const negativeWords = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disappointed'];

    let positiveCount = 0;
    let negativeCount = 0;

    for (const message of messages) {
      const content = message.content.toLowerCase();
      positiveWords.forEach(word => {
        if (content.includes(word)) positiveCount++;
      });
      negativeWords.forEach(word => {
        if (content.includes(word)) negativeCount++;
      });
    }

    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
  }

  private calculateSatisfactionScore(sentiment: string, resolved: boolean, intent: string): number {
    let score = 3.0; // Base score

    if (sentiment === 'positive') score += 1.5;
    else if (sentiment === 'negative') score -= 1.5;

    if (resolved) score += 1.0;
    if (intent === 'complaint' && !resolved) score -= 1.0;

    return Math.max(1.0, Math.min(5.0, score));
  }

  private extractKeyTopics(messages: ConversationMessage[]): string[] {
    const topics = new Set<string>();
    const topicKeywords = {
      'Appointment Booking': ['appointment', 'book', 'schedule', 'reservation'],
      'Business Hours': ['hours', 'open', 'close', 'time'],
      'Services': ['service', 'treatment', 'procedure'],
      'Pricing': ['price', 'cost', 'how much', 'fee'],
      'Menu/Food': ['menu', 'food', 'order', 'delivery'],
      'Contact Info': ['phone', 'email', 'address', 'contact'],
    };

    for (const message of messages) {
      const content = message.content.toLowerCase();
      for (const [topic, keywords] of Object.entries(topicKeywords)) {
        if (keywords.some(keyword => content.includes(keyword))) {
          topics.add(topic);
        }
      }
    }

    return Array.from(topics);
  }
}

export default AIConversationEngine;