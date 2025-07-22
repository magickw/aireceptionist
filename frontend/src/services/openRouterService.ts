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
      const response = await fetch(`${this.baseURL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'http://localhost:3002',
          'X-Title': 'AI Receptionist Pro',
        },
        body: JSON.stringify({
          model: model,
          messages: messages,
          temperature: 0.7,
          max_tokens: 500,
        }),
      });

      if (!response.ok) {
        throw new Error(`OpenRouter API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.choices[0]?.message?.content || 'I apologize, I had trouble processing that request.';
    } catch (error) {
      console.error('OpenRouter API error:', error);
      return 'I apologize, I\'m experiencing technical difficulties. Please try again or speak with a human agent.';
    }
  }

  async generateSmartResponse(userMessage: string, context: any): Promise<string> {
    const systemPrompt = `You are an AI receptionist for a ${context.businessType || 'business'}. 
Your role is to:
- Help customers book appointments
- Answer questions about services and hours
- Take messages
- Be friendly and professional

Business context:
- Type: ${context.businessType || 'general business'}
- Services: ${context.services?.map((s: any) => s.name).join(', ') || 'various services'}
- Hours: ${this.formatBusinessHours(context.operatingHours)}

Respond naturally and helpfully to the customer's message.`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userMessage }
    ];

    return await this.generateResponse(messages);
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