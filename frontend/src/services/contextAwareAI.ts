import { ConversationMessage, ConversationContext, AIResponse, AIAction, Service, OrderItem, CallSummary } from '@/types/ai';
import OpenRouterService from './openRouterService';

/**
 * Enhanced AI service that maintains conversation context and ensures contextual continuity
 */
class ContextAwareAI {
  private openRouterService: OpenRouterService;
  private businessContext: Record<string, unknown>;
  
  constructor(businessContext: Record<string, unknown>) {
    this.businessContext = businessContext;
    this.openRouterService = new OpenRouterService();
  }

  /**
   * Process a user message with full conversation history awareness
   */
  public async processMessage(message: string, context: ConversationContext, conversationHistory: ConversationMessage[]): Promise<AIResponse> {
    console.log('🧠 ContextAwareAI - Processing message:', message);
    console.log('🧠 ContextAwareAI - Current context:', context);
    console.log('🧠 ContextAwareAI - Conversation history:', conversationHistory);
    
    // Extract entities from the message (name, date, time, etc.)
    const entities = this.extractEntities(message, context);
    
    // Update context with any new entities found
    this.updateContext(context, entities);
    
    try {
      // Generate response using OpenRouter with full conversation history
      const response = await this.openRouterService.generateSmartResponse(
        message,
        context.businessContext || this.businessContext,
        conversationHistory,
        context
      );
      
      console.log('🧠 ContextAwareAI - Generated response:', response);
      
      // Determine appropriate actions based on context and message
      const actions = this.determineActions(message, context, entities);
      
      return {
        message: response,
        confidence: 0.95, // High confidence with context-aware model
        intent: this.determineIntent(message, context),
        entities,
        actions
      };
    } catch (error) {
      console.error('🧠 ContextAwareAI - Error generating response:', error);
      
      // Fallback response that maintains context
      return this.generateFallbackResponse(message, context, conversationHistory);
    }
  }
  
  /**
   * Extract entities from user message
   */
  private extractEntities(message: string, context: ConversationContext): Record<string, unknown> {
    const entities: Record<string, unknown> = {};
    
    // Extract name if not already known
    if (!context.customerInfo.name) {
      const nameMatch = message.match(/(?:my name is|i'm|i am|this is)\s+([a-zA-Z\s]+)/i);
      if (nameMatch && nameMatch[1]) {
        entities.name = nameMatch[1].trim();
      }
    }
    
    // Extract phone if not already known
    if (!context.customerInfo.phone) {
      const phoneMatch = message.match(/(\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]?\d{4})/);
      if (phoneMatch && phoneMatch[1]) {
        entities.phone = phoneMatch[1];
      }
    }
    
    // Extract email if not already known
    if (!context.customerInfo.email) {
      const emailMatch = message.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      if (emailMatch && emailMatch[1]) {
        entities.email = emailMatch[1];
      }
    }
    
    // Extract date if in booking context and not already known
    if (context.intent === 'booking' && context.bookingInfo && !context.bookingInfo.date) {
      const dateMatch = message.match(/(today|tomorrow|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}\/\d{1,2}|\d{1,2}-\d{1,2})/i);
      if (dateMatch && dateMatch[1]) {
        entities.date = dateMatch[1];
      }
    }
    
    // Extract time if in booking context and not already known
    if (context.intent === 'booking' && context.bookingInfo && !context.bookingInfo.time) {
      const timeMatch = message.match(/(\d{1,2}:\d{2}\s*(am|pm)?|\d{1,2}\s*(am|pm)|noon|morning|afternoon|evening)/i);
      if (timeMatch && timeMatch[1]) {
        entities.time = timeMatch[1];
      }
    }
    
    return entities;
  }
  
  /**
   * Update conversation context with new entities
   */
  private updateContext(context: ConversationContext, entities: Record<string, any>): void {
    // Update customer info
    if (entities.name) context.customerInfo.name = entities.name.trim();
    if (entities.phone) context.customerInfo.phone = entities.phone;
    if (entities.email) context.customerInfo.email = entities.email;
    
    // Update booking info if in booking context
    if (context.intent === 'booking') {
      if (!context.bookingInfo) {
        context.bookingInfo = { completed: false };
      }
      
      if (entities.date) context.bookingInfo.date = entities.date;
      if (entities.time) context.bookingInfo.time = entities.time;
      
      // Check if booking is complete
      context.bookingInfo.completed = !!(context.customerInfo.name && 
                                      context.customerInfo.phone && 
                                      context.bookingInfo.date && 
                                      context.bookingInfo.time);
    }
    
    // Update order info if in ordering context
    if (context.intent === 'ordering') {
      if (!context.orderInfo) {
        context.orderInfo = { items: [], completed: false };
      }
      
      // Check if order is complete
      context.orderInfo.completed = !!(context.customerInfo.name && 
                                    context.customerInfo.phone && 
                                    context.orderInfo.items.length > 0);
    }
  }
  
  /**
   * Determine intent from message and context
   */
  private determineIntent(message: string, context: ConversationContext): string {
    // If we already have a specific intent that's not 'unknown', keep it
    if (context.intent !== 'unknown') {
      return context.intent;
    }
    
    const lowerMessage = message.toLowerCase();
    
    // Check for booking intent
    if (lowerMessage.includes('book') || 
        lowerMessage.includes('appointment') || 
        lowerMessage.includes('schedule') || 
        lowerMessage.includes('reservation') || 
        lowerMessage.includes('table') ||
        lowerMessage.includes('dinner') ||
        lowerMessage.includes('lunch')) {
      return 'booking';
    }
    
    // Check for ordering intent
    if (lowerMessage.includes('order') || 
        lowerMessage.includes('food') || 
        lowerMessage.includes('delivery') || 
        lowerMessage.includes('takeout')) {
      return 'ordering';
    }
    
    // Check for inquiry intent
    if (lowerMessage.includes('hours') || 
        lowerMessage.includes('open') || 
        lowerMessage.includes('price') || 
        lowerMessage.includes('cost') || 
        lowerMessage.includes('menu') || 
        lowerMessage.includes('service')) {
      return 'inquiry';
    }
    
    // Check for complaint intent
    if (lowerMessage.includes('problem') || 
        lowerMessage.includes('issue') || 
        lowerMessage.includes('complaint') || 
        lowerMessage.includes('unhappy')) {
      return 'complaint';
    }
    
    // Default to unknown if no clear intent
    return 'unknown';
  }
  
  /**
   * Determine actions based on context and message
   */
  private determineActions(message: string, context: ConversationContext, entities: Record<string, unknown>): AIAction[] {
    const actions = [];
    
    // If booking is complete, create a booking action
    if (context.intent === 'booking' && context.bookingInfo?.completed) {
      actions.push({
        type: 'create_booking',
        data: {
          customerName: context.customerInfo.name,
          customerPhone: context.customerInfo.phone,
          customerEmail: context.customerInfo.email,
          service: context.bookingInfo.service || 'General Appointment',
          date: context.bookingInfo.date,
          time: context.bookingInfo.time,
          duration: context.bookingInfo.duration || 60
        },
        completed: false
      });
    }
    
    // If order is complete, create an order action
    if (context.intent === 'ordering' && context.orderInfo?.completed) {
      actions.push({
        type: 'create_order',
        data: {
          customerName: context.customerInfo.name,
          customerPhone: context.customerInfo.phone,
          items: context.orderInfo.items,
          total: context.orderInfo.total
        },
        completed: false
      });
    }
    
    // If it's a complaint, create a transfer action
    if (context.intent === 'complaint') {
      actions.push({
        type: 'transfer_call',
        data: {
          department: 'customer_service',
          reason: 'complaint'
        },
        completed: false
      });
    }
    
    return actions;
  }
  
  /**
   * Generate a fallback response that maintains context
   */
  private generateFallbackResponse(message: string, context: ConversationContext, history: ConversationMessage[]): AIResponse {
    let response = "I'm here to help you. ";
    
    // Personalize if we know the customer's name
    if (context.customerInfo.name) {
      response = `${context.customerInfo.name}, I'm here to help you. `;
    }
    
    // Add context-specific responses
    if (context.intent === 'booking') {
      if (!context.bookingInfo?.date) {
        response += "What date would you like to book your appointment?";
      } else if (!context.bookingInfo?.time) {
        response += "What time would work best for you on " + context.bookingInfo.date + "?";
      } else {
        response += "I've noted your appointment request for " + context.bookingInfo.date + " at " + context.bookingInfo.time + ". Is there anything else you need?";
      }
    } else if (context.intent === 'ordering') {
      response += "What would you like to order today?";
    } else {
      response += "How can I assist you today?";
    }
    
    return {
      message: response,
      confidence: 0.7,
      intent: context.intent,
      entities: {},
      actions: []
    };
  }

  /**
   * Generate a summary of the call based on conversation messages
   */
  public generateCallSummary(messages: ConversationMessage[], context?: ConversationContext): CallSummary {
    console.log('🧠 ContextAwareAI - Generating call summary');
    
    // Extract customer messages for analysis
    const customerMessages = messages.filter(msg => msg.sender === 'customer').map(msg => msg.content);
    const aiMessages = messages.filter(msg => msg.sender === 'ai').map(msg => msg.content);
    
    // Calculate satisfaction score based on conversation flow
    let satisfactionScore = 7; // Default to slightly above average
    
    // Analyze if customer needs were addressed
    const resolved = this.analyzeResolution(messages, context);
    if (resolved) satisfactionScore += 2;
    
    // Extract key topics from conversation
    const keyTopics = this.extractKeyTopics(messages);
    
    // Analyze sentiment
    const sentiment = this.analyzeSentiment(customerMessages);
    if (sentiment === 'positive') satisfactionScore = Math.min(10, satisfactionScore + 1);
    if (sentiment === 'negative') satisfactionScore = Math.max(1, satisfactionScore - 2);
    
    // Generate summary text
    const summary = this.generateSummaryText(messages, context);
    
    return {
      satisfactionScore,
      resolved,
      keyTopics,
      sentiment,
      summary
    };
  }
  
  /**
   * Analyze if the conversation reached a resolution
   */
  private analyzeResolution(messages: ConversationMessage[], context?: ConversationContext): boolean {
    // Check if booking or order was completed
    if (context?.bookingInfo?.completed || context?.orderInfo?.completed) {
      return true;
    }
    
    // Check for positive closing statements
    const lastCustomerMessages = messages
      .filter(msg => msg.sender === 'customer')
      .slice(-2);
      
    for (const msg of lastCustomerMessages) {
      const text = msg.content.toLowerCase();
      if (text.includes('thank you') || 
          text.includes('thanks') || 
          text.includes('great') || 
          text.includes('perfect') || 
          text.includes('sounds good')) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * Extract key topics from conversation
   */
  private extractKeyTopics(messages: ConversationMessage[]): string[] {
    const topics = new Set<string>();
    
    // Check for booking-related topics
    if (messages.some(msg => 
      msg.content.toLowerCase().includes('book') || 
      msg.content.toLowerCase().includes('appointment') || 
      msg.content.toLowerCase().includes('schedule'))) {
      topics.add('Booking');
    }
    
    // Check for order-related topics
    if (messages.some(msg => 
      msg.content.toLowerCase().includes('order') || 
      msg.content.toLowerCase().includes('food') || 
      msg.content.toLowerCase().includes('menu'))) {
      topics.add('Ordering');
    }
    
    // Check for information-related topics
    if (messages.some(msg => 
      msg.content.toLowerCase().includes('hour') || 
      msg.content.toLowerCase().includes('open') || 
      msg.content.toLowerCase().includes('price') || 
      msg.content.toLowerCase().includes('cost'))) {
      topics.add('Information');
    }
    
    // Check for support-related topics
    if (messages.some(msg => 
      msg.content.toLowerCase().includes('problem') || 
      msg.content.toLowerCase().includes('issue') || 
      msg.content.toLowerCase().includes('help') || 
      msg.content.toLowerCase().includes('support'))) {
      topics.add('Support');
    }
    
    return Array.from(topics);
  }
  
  /**
   * Analyze sentiment of customer messages
   */
  private analyzeSentiment(customerMessages: string[]): 'positive' | 'neutral' | 'negative' {
    const positiveWords = ['thank', 'thanks', 'good', 'great', 'excellent', 'perfect', 'awesome', 'appreciate'];
    const negativeWords = ['bad', 'terrible', 'awful', 'horrible', 'disappointed', 'unhappy', 'issue', 'problem', 'wrong'];
    
    let positiveCount = 0;
    let negativeCount = 0;
    
    for (const message of customerMessages) {
      const lowerMessage = message.toLowerCase();
      
      for (const word of positiveWords) {
        if (lowerMessage.includes(word)) positiveCount++;
      }
      
      for (const word of negativeWords) {
        if (lowerMessage.includes(word)) negativeCount++;
      }
    }
    
    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
  }
  
  /**
   * Generate a text summary of the conversation
   */
  private generateSummaryText(messages: ConversationMessage[], context?: ConversationContext): string {
    let summary = 'Customer called ';
    
    // Add context information
    if (context?.intent === 'booking') {
      summary += 'to make a booking';
      if (context.bookingInfo?.service) {
        summary += ` for ${context.bookingInfo.service}`;
      }
      if (context.bookingInfo?.date && context.bookingInfo?.time) {
        summary += ` on ${context.bookingInfo.date} at ${context.bookingInfo.time}`;
      }
      summary += '.';
    } else if (context?.intent === 'ordering') {
      summary += 'to place an order';
      if (context.orderInfo?.items.length) {
        summary += ` for ${context.orderInfo.items.length} item(s)`;
      }
      summary += '.';
    } else if (context?.intent === 'inquiry') {
      summary += 'to inquire about our services or information.';
    } else if (context?.intent === 'complaint') {
      summary += 'with a complaint or issue that needed resolution.';
    } else {
      summary += 'for general assistance.';
    }
    
    // Add customer information if available
    if (context?.customerInfo.name) {
      summary += ` Customer identified as ${context.customerInfo.name}`;
      if (context.customerInfo.phone) {
        summary += ` (${context.customerInfo.phone})`;
      }
      summary += '.';
    }
    
    return summary;
  }
}

export default ContextAwareAI;