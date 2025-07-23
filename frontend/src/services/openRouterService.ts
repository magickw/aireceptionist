// OpenRouter AI Service for making API calls
class OpenRouterService {
  private apiKey: string;
  private baseURL: string;

  constructor() {
    this.apiKey = process.env.NEXT_PUBLIC_OPENROUTER_API_KEY || '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';
    this.baseURL = 'https://openrouter.ai/api/v1';
  }

  async generateResponse(messages: any[], model: string = 'openai/gpt-3.5-turbo'): Promise<string> {
    try {
      console.log('Making OpenRouter API call with messages:', messages);
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(`${this.baseURL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'http://localhost:3003', // Updated port
          'X-Title': 'AI Receptionist Pro',
        },
        body: JSON.stringify({
          model: model,
          messages: messages,
          temperature: 0.7,
          max_tokens: 500,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      console.log('OpenRouter response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('OpenRouter API error response:', errorText);
        throw new Error(`OpenRouter API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('OpenRouter API response data:', data);
      
      const aiMessage = data.choices?.[0]?.message?.content;
      console.log('Extracted AI message:', aiMessage);
      
      if (!aiMessage) {
        console.error('No message content in API response, data structure:', data);
        throw new Error('No message content in API response');
      }
      
      return aiMessage;
    } catch (error) {
      console.error('OpenRouter API error:', error);
      if (error.name === 'AbortError') {
        console.error('Request timed out after 10 seconds');
      }
      // Return a more helpful fallback based on the user's message
      return this.generateFallbackResponse(messages);
    }
  }

  private generateFallbackResponse(messages: any[]): string {
    const userMessage = messages[messages.length - 1]?.content?.toLowerCase() || '';
    
    // Basic intent detection for fallback
    if (userMessage.includes('book') || userMessage.includes('appointment') || userMessage.includes('schedule')) {
      return "I'd be happy to help you book an appointment! May I get your name and what service you're interested in?";
    }
    
    if (userMessage.includes('hours') || userMessage.includes('open') || userMessage.includes('close')) {
      return "We're open Monday through Friday from 9 AM to 5 PM. Would you like to schedule an appointment?";
    }
    
    if (userMessage.includes('service') || userMessage.includes('price') || userMessage.includes('cost')) {
      return "I'd be happy to tell you about our services! What specific service are you interested in learning about?";
    }
    
    if (userMessage.includes('hello') || userMessage.includes('hi')) {
      return "Hello! Welcome to our business. How can I help you today?";
    }
    
    // General fallback
    return "Thank you for calling! I'm here to help with appointments, questions about our services, or connecting you with the right person. How can I assist you today?";
  }

  async generateSmartResponse(userMessage: string, context: any): Promise<string> {
    try {
      console.log('Generating smart response for message:', userMessage);
      console.log('Business context:', context);

      // Handle case where context might be undefined or missing data
      const businessType = context?.businessType || context?.type || 'business';
      const services = context?.services || [];
      const operatingHours = context?.operatingHours || {};

      const systemPrompt = `You are an AI receptionist for a ${businessType}. 
Your role is to:
- Help customers make reservations and bookings
- Answer questions about services, menu, and hours
- Take orders (if restaurant)
- Handle inquiries professionally
- Keep responses concise and helpful

Business Details:
- Type: ${businessType}
- Available Services: ${services.map((s: any) => s.name).join(', ') || 'various services available'}
- Operating Hours: ${this.formatBusinessHours(operatingHours)}

${businessType === 'restaurant' ? `
Restaurant-Specific Instructions:
- For table reservations, ask for: party size, date, time, and contact name
- For food orders, offer menu items and take detailed orders
- Always be welcoming and enthusiastic about dining experiences
- Ask about dietary restrictions or preferences when relevant
` : businessType === 'salon' ? `
Salon-Specific Instructions:
- For appointments, ask for: service type, preferred date/time, and contact info
- Offer consultation for new customers
- Ask about hair type or specific styling needs
` : businessType === 'medical' ? `
Medical Practice Instructions:
- For appointments, ask for: reason for visit, preferred doctor, urgency level
- Be professional and reassuring
- Collect patient information carefully
` : ''}

Important Guidelines:
- Always match your responses to the business type (${businessType})
- Be warm, professional, and helpful
- Ask clarifying questions to gather complete information
- If unsure about availability, offer to check and call back

Respond naturally to the customer's request. Keep responses to 1-2 sentences when possible.`;

      const messages = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage }
      ];

      console.log('Sending request to OpenRouter...');
      const response = await this.generateResponse(messages);
      console.log('OpenRouter response received:', response);
      return response;
      
    } catch (error) {
      console.error('Error in generateSmartResponse:', error);
      return this.generateFallbackResponse([{ content: userMessage }]);
    }
  }

  private formatBusinessHours(hours: any): string {
    if (!hours) return 'Please call for our current hours';
    
    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const openDays = [];
    
    for (let i = 0; i < 7; i++) {
      const dayHours = hours[i];
      if (dayHours && !dayHours.closed) {
        openDays.push(`${daysOfWeek[i]} ${dayHours.open}:00-${dayHours.close}:00`);
      }
    }
    
    return openDays.length > 0 ? openDays.join(', ') : 'Please call for hours';
  }
}

export default OpenRouterService;