const AIConversationEngine = require('../services/aiConversationEngine');

describe('AI Conversation Engine', () => {
  let aiEngine;
  let mockBusinessContext;

  beforeEach(() => {
    mockBusinessContext = {
      type: 'restaurant',
      services: [
        { id: '1', name: 'Dinner Reservation', description: 'Table booking' },
        { id: '2', name: 'Takeout Order', description: 'Food ordering' }
      ],
      operatingHours: {
        0: { open: 10, close: 22, closed: false }, // Sunday
        1: { open: 10, close: 22, closed: false }, // Monday
        2: { open: 10, close: 22, closed: false }, // Tuesday
        3: { open: 10, close: 22, closed: false }, // Wednesday
        4: { open: 10, close: 22, closed: false }, // Thursday
        5: { open: 10, close: 22, closed: false }, // Friday
        6: { open: 10, close: 22, closed: false }  // Saturday
      },
      menu: [
        { id: '1', name: 'Caesar Salad', price: 12.99, available: true },
        { id: '2', name: 'Grilled Chicken', price: 18.99, available: true }
      ]
    };

    aiEngine = new AIConversationEngine(mockBusinessContext);
  });

  describe('Intent Detection', () => {
    it('should detect booking intent', () => {
      const message = "I'd like to book a table for tonight";
      const intent = aiEngine.detectIntent(message);
      expect(intent).toBe('booking');
    });

    it('should detect ordering intent', () => {
      const message = "I want to order some food for delivery";
      const intent = aiEngine.detectIntent(message);
      expect(intent).toBe('ordering');
    });

    it('should detect inquiry intent', () => {
      const message = "What are your opening hours today?";
      const intent = aiEngine.detectIntent(message);
      expect(intent).toBe('inquiry');
    });

    it('should detect complaint intent', () => {
      const message = "I have a complaint about my last order";
      const intent = aiEngine.detectIntent(message);
      expect(intent).toBe('complaint');
    });

    it('should return unknown for unclear messages', () => {
      const message = "Hello there";
      const intent = aiEngine.detectIntent(message);
      expect(intent).toBe('unknown');
    });
  });

  describe('Entity Extraction', () => {
    it('should extract name entities', () => {
      const message = "My name is John Smith";
      const entities = aiEngine.extractEntities(message);
      expect(entities.name).toBe('John Smith');
    });

    it('should extract phone number entities', () => {
      const message = "You can reach me at 555-123-4567";
      const entities = aiEngine.extractEntities(message);
      expect(entities.phone).toMatch(/555[-.\s]?123[-.\s]?4567/);
    });

    it('should extract email entities', () => {
      const message = "My email is john@example.com";
      const entities = aiEngine.extractEntities(message);
      expect(entities.email).toBe('john@example.com');
    });

    it('should extract time entities', () => {
      const message = "Can I book for 7:30 PM?";
      const entities = aiEngine.extractEntities(message);
      expect(entities.time).toMatch(/7:30.*pm/i);
    });

    it('should extract date entities', () => {
      const message = "I need a reservation for tomorrow";
      const entities = aiEngine.extractEntities(message);
      expect(entities.date).toBe('tomorrow');
    });
  });

  describe('Context Management', () => {
    let conversationContext;

    beforeEach(() => {
      conversationContext = {
        customerInfo: {},
        intent: 'unknown',
        businessContext: {
          businessType: 'restaurant',
          services: mockBusinessContext.services,
          operatingHours: mockBusinessContext.operatingHours,
          menu: mockBusinessContext.menu
        }
      };
    });

    it('should update customer info from entities', () => {
      const entities = {
        name: 'John Doe',
        phone: '555-123-4567',
        email: 'john@example.com'
      };

      aiEngine.updateContext(conversationContext, entities, 'booking');

      expect(conversationContext.customerInfo.name).toBe('John Doe');
      expect(conversationContext.customerInfo.phone).toBe('555-123-4567');
      expect(conversationContext.customerInfo.email).toBe('john@example.com');
    });

    it('should update intent when detected', () => {
      aiEngine.updateContext(conversationContext, {}, 'booking');
      expect(conversationContext.intent).toBe('booking');
    });

    it('should initialize booking info for booking intent', () => {
      const entities = { service: 'dinner', date: 'tomorrow', time: '7pm' };
      
      aiEngine.updateContext(conversationContext, entities, 'booking');
      
      expect(conversationContext.bookingInfo).toBeDefined();
      expect(conversationContext.bookingInfo.service).toBe('dinner');
      expect(conversationContext.bookingInfo.date).toBe('tomorrow');
      expect(conversationContext.bookingInfo.time).toBe('7pm');
    });

    it('should mark booking as completed when all info is present', () => {
      conversationContext.customerInfo = {
        name: 'John Doe',
        phone: '555-123-4567'
      };
      
      const entities = { service: 'dinner', date: 'tomorrow', time: '7pm' };
      
      aiEngine.updateContext(conversationContext, entities, 'booking');
      
      expect(conversationContext.bookingInfo.completed).toBe(true);
    });
  });

  describe('Action Determination', () => {
    let conversationContext;

    beforeEach(() => {
      conversationContext = {
        customerInfo: {
          name: 'John Doe',
          phone: '555-123-4567'
        },
        intent: 'unknown',
        businessContext: {
          businessType: 'restaurant',
          services: mockBusinessContext.services,
          operatingHours: mockBusinessContext.operatingHours
        }
      };
    });

    it('should create booking action when booking is complete', () => {
      conversationContext.intent = 'booking';
      conversationContext.bookingInfo = {
        service: 'dinner',
        date: 'tomorrow',
        time: '7pm',
        completed: true
      };

      const actions = aiEngine.determineActions('booking', {}, conversationContext);
      
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe('create_booking');
      expect(actions[0].data.customerName).toBe('John Doe');
      expect(actions[0].data.service).toBe('dinner');
    });

    it('should create transfer action for complaints', () => {
      const actions = aiEngine.determineActions('complaint', {}, conversationContext);
      
      expect(actions).toHaveLength(1);
      expect(actions[0].type).toBe('transfer_call');
      expect(actions[0].data.reason).toBe('complaint');
    });

    it('should return empty array for incomplete bookings', () => {
      conversationContext.intent = 'booking';
      conversationContext.bookingInfo = {
        service: 'dinner',
        completed: false
      };

      const actions = aiEngine.determineActions('booking', {}, conversationContext);
      
      expect(actions).toHaveLength(0);
    });
  });

  describe('Response Generation', () => {
    let conversationContext;

    beforeEach(() => {
      conversationContext = {
        customerInfo: {},
        intent: 'unknown',
        businessContext: {
          businessType: 'restaurant',
          services: mockBusinessContext.services,
          operatingHours: mockBusinessContext.operatingHours
        }
      };
    });

    it('should ask for name when booking without customer info', () => {
      const response = aiEngine.generateBookingResponse({}, conversationContext, 'restaurant');
      
      expect(response).toContain('name');
      expect(response.toLowerCase()).toContain('appointment');
    });

    it('should ask for phone when name is provided but phone is missing', () => {
      conversationContext.customerInfo.name = 'John Doe';
      
      const response = aiEngine.generateBookingResponse({}, conversationContext, 'restaurant');
      
      expect(response).toContain('phone');
    });

    it('should provide confirmation when booking is complete', () => {
      conversationContext.customerInfo = {
        name: 'John Doe',
        phone: '555-123-4567'
      };
      conversationContext.bookingInfo = {
        service: 'dinner',
        date: 'tomorrow',
        time: '7pm',
        completed: true
      };

      const response = aiEngine.generateBookingResponse({}, conversationContext, 'restaurant');
      
      expect(response).toContain('Perfect');
      expect(response).toContain('John Doe');
      expect(response).toContain('dinner');
    });
  });

  describe('Full Conversation Flow', () => {
    it('should handle a complete booking conversation', async () => {
      let context = {
        customerInfo: {},
        intent: 'unknown',
        businessContext: {
          businessType: 'restaurant',
          services: mockBusinessContext.services,
          operatingHours: mockBusinessContext.operatingHours
        }
      };

      // Step 1: Initial booking request
      let result = await aiEngine.processMessage("I'd like to book a table", context);
      expect(result.intent).toBe('booking');
      expect(result.message).toContain('name');

      // Step 2: Provide name
      result = await aiEngine.processMessage("My name is John Doe", context);
      expect(context.customerInfo.name).toBe('John Doe');
      expect(result.message).toContain('phone');

      // Step 3: Provide phone
      result = await aiEngine.processMessage("555-123-4567", context);
      expect(context.customerInfo.phone).toBe('555-123-4567');

      // Step 4: Provide service, date, and time
      result = await aiEngine.processMessage("I want dinner tomorrow at 7pm", context);
      
      expect(context.bookingInfo).toBeDefined();
      expect(context.bookingInfo.completed).toBe(true);
      expect(result.actions).toHaveLength(1);
      expect(result.actions[0].type).toBe('create_booking');
    });
  });

  describe('Confidence Calculation', () => {
    it('should calculate higher confidence for clear intents', () => {
      const confidence1 = aiEngine.calculateConfidence("book table", 'booking', { name: 'John' });
      const confidence2 = aiEngine.calculateConfidence("hello", 'unknown', {});
      
      expect(confidence1).toBeGreaterThan(confidence2);
    });

    it('should increase confidence with more entities', () => {
      const confidence1 = aiEngine.calculateConfidence("book table", 'booking', {});
      const confidence2 = aiEngine.calculateConfidence("book table", 'booking', { 
        name: 'John', 
        phone: '555-1234',
        time: '7pm' 
      });
      
      expect(confidence2).toBeGreaterThan(confidence1);
    });

    it('should cap confidence at 1.0', () => {
      const confidence = aiEngine.calculateConfidence("book table", 'booking', { 
        name: 'John', 
        phone: '555-1234',
        email: 'john@example.com',
        time: '7pm',
        date: 'tomorrow'
      });
      
      expect(confidence).toBeLessThanOrEqual(1.0);
    });
  });
});