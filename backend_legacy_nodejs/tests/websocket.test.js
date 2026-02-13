const WebSocket = require('ws');
const websocketManager = require('../services/websocketManager');
const logger = require('../utils/logger');

describe('WebSocket Manager', () => {
  let mockServer;
  let wsClients = [];

  beforeAll(() => {
    // Create a mock HTTP server
    mockServer = {
      on: jest.fn(),
      close: jest.fn()
    };
    
    // Initialize WebSocket manager
    websocketManager.initialize(mockServer);
  });

  afterAll(() => {
    // Clean up
    websocketManager.shutdown();
    wsClients.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    });
  });

  describe('Client Connection Management', () => {
    it('should generate unique client IDs', () => {
      const id1 = websocketManager.generateClientId();
      const id2 = websocketManager.generateClientId();
      
      expect(id1).toMatch(/^client_\d+_[a-z0-9]{9}$/);
      expect(id2).toMatch(/^client_\d+_[a-z0-9]{9}$/);
      expect(id1).not.toBe(id2);
    });

    it('should track client connections', () => {
      const initialStats = websocketManager.getStats();
      expect(initialStats).toHaveProperty('connectedClients');
      expect(initialStats).toHaveProperty('activeCalls');
      expect(initialStats).toHaveProperty('totalParticipants');
    });
  });

  describe('Call Session Management', () => {
    let mockWs1, mockWs2;
    let clientId1, clientId2;

    beforeEach(() => {
      // Create mock WebSocket connections
      mockWs1 = {
        send: jest.fn(),
        readyState: WebSocket.OPEN,
        clientId: 'test-client-1',
        isAlive: true
      };
      
      mockWs2 = {
        send: jest.fn(),
        readyState: WebSocket.OPEN,
        clientId: 'test-client-2',
        isAlive: true
      };

      clientId1 = mockWs1.clientId;
      clientId2 = mockWs2.clientId;

      // Add to clients map
      websocketManager.clients.set(clientId1, { ws: mockWs1, id: clientId1 });
      websocketManager.clients.set(clientId2, { ws: mockWs2, id: clientId2 });
    });

    afterEach(() => {
      // Clean up test data
      websocketManager.clients.delete(clientId1);
      websocketManager.clients.delete(clientId2);
      websocketManager.callSessions.clear();
    });

    it('should handle join call requests', () => {
      const callId = 'test-call-123';
      
      websocketManager.handleJoinCall(clientId1, {
        callId,
        role: 'caller'
      });

      expect(websocketManager.callSessions.has(callId)).toBe(true);
      
      const callSession = websocketManager.callSessions.get(callId);
      expect(callSession.participants.has(clientId1)).toBe(true);
      expect(callSession.participants.get(clientId1).role).toBe('caller');
      
      expect(mockWs1.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"call_joined"')
      );
    });

    it('should notify other participants when someone joins', () => {
      const callId = 'test-call-123';
      
      // First client joins
      websocketManager.handleJoinCall(clientId1, { callId, role: 'caller' });
      
      // Second client joins
      websocketManager.handleJoinCall(clientId2, { callId, role: 'receiver' });
      
      // Check that first client was notified about second client joining
      expect(mockWs1.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"participant_joined"')
      );
    });

    it('should handle leave call requests', () => {
      const callId = 'test-call-123';
      
      // Both clients join
      websocketManager.handleJoinCall(clientId1, { callId });
      websocketManager.handleJoinCall(clientId2, { callId });
      
      // First client leaves
      websocketManager.handleLeaveCall(clientId1, { callId });
      
      const callSession = websocketManager.callSessions.get(callId);
      expect(callSession.participants.has(clientId1)).toBe(false);
      expect(callSession.participants.has(clientId2)).toBe(true);
      
      // Second client should be notified
      expect(mockWs2.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"participant_left"')
      );
    });

    it('should clean up empty call sessions', () => {
      const callId = 'test-call-123';
      
      // Client joins and leaves
      websocketManager.handleJoinCall(clientId1, { callId });
      websocketManager.handleLeaveCall(clientId1, { callId });
      
      expect(websocketManager.callSessions.has(callId)).toBe(false);
    });

    it('should handle audio data broadcasting', () => {
      const callId = 'test-call-123';
      const audioData = 'mock-audio-data';
      
      // Both clients join call
      websocketManager.handleJoinCall(clientId1, { callId });
      websocketManager.handleJoinCall(clientId2, { callId });
      
      // Client 1 sends audio data
      websocketManager.handleAudioData(clientId1, {
        callId,
        audioData,
        format: 'wav'
      });
      
      // Client 2 should receive the audio data
      expect(mockWs2.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"audio_data"')
      );
      
      // Client 1 should not receive their own audio back
      expect(mockWs1.send).not.toHaveBeenCalledWith(
        expect.stringContaining('"type":"audio_data"')
      );
    });

    it('should handle call control messages', () => {
      const callId = 'test-call-123';
      
      // Both clients join call
      websocketManager.handleJoinCall(clientId1, { callId });
      websocketManager.handleJoinCall(clientId2, { callId });
      
      // Client 1 sends mute control
      websocketManager.handleCallControl(clientId1, {
        callId,
        action: 'mute'
      });
      
      // Both clients should receive the control message
      expect(mockWs1.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"call_control"')
      );
      expect(mockWs2.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"call_control"')
      );
    });
  });

  describe('Message Handling', () => {
    let mockWs;
    let clientId;

    beforeEach(() => {
      mockWs = {
        send: jest.fn(),
        readyState: WebSocket.OPEN,
        clientId: 'test-client',
        isAlive: true
      };
      
      clientId = mockWs.clientId;
      websocketManager.clients.set(clientId, { ws: mockWs, id: clientId });
    });

    afterEach(() => {
      websocketManager.clients.delete(clientId);
    });

    it('should handle ping messages', () => {
      const message = JSON.stringify({ type: 'ping' });
      
      websocketManager.handleMessage(mockWs, message);
      
      expect(mockWs.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"pong"')
      );
    });

    it('should handle unknown message types gracefully', () => {
      const message = JSON.stringify({ type: 'unknown_type' });
      
      expect(() => {
        websocketManager.handleMessage(mockWs, message);
      }).not.toThrow();
    });

    it('should handle malformed JSON gracefully', () => {
      const malformedMessage = '{"type": invalid json';
      
      expect(() => {
        websocketManager.handleMessage(mockWs, malformedMessage);
      }).not.toThrow();
    });
  });

  describe('Statistics and Health', () => {
    it('should provide accurate statistics', () => {
      const stats = websocketManager.getStats();
      
      expect(stats).toHaveProperty('connectedClients');
      expect(stats).toHaveProperty('activeCalls');
      expect(stats).toHaveProperty('totalParticipants');
      expect(typeof stats.connectedClients).toBe('number');
      expect(typeof stats.activeCalls).toBe('number');
      expect(typeof stats.totalParticipants).toBe('number');
    });
  });
});