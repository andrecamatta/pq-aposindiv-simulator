import axios from 'axios';
import type { SimulatorState, SimulatorResults, MortalityTable, WebSocketMessage } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API REST endpoints
export const apiService = {
  async getMortalityTables(): Promise<MortalityTable[]> {
    const response = await api.get('/mortality-tables');
    return response.data.tables || response.data;
  },

  async getDefaultState(): Promise<SimulatorState> {
    const response = await api.get('/default-state');
    return response.data;
  },

  async calculate(state: SimulatorState): Promise<SimulatorResults> {
    const response = await api.post('/calculate', state);
    return response.data;
  },

  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};

// WebSocket client
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private clientId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, (data: any) => void> = new Map();

  constructor(clientId?: string) {
    this.clientId = clientId || this.generateClientId();
  }

  private generateClientId(): string {
    return 'client_' + Math.random().toString(36).substr(2, 9);
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `ws://localhost:8001/ws/${this.clientId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket conectado');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket desconectado:', event.code, event.reason);
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('Erro WebSocket:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Tentativa de reconexão ${this.reconnectAttempts}/${this.maxReconnectAttempts} em ${delay}ms`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, delay);
    }
  }

  private handleMessage(message: WebSocketMessage) {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message.data || message);
    }
  }

  on(messageType: string, handler: (data: any) => void) {
    this.messageHandlers.set(messageType, handler);
  }

  off(messageType: string) {
    this.messageHandlers.delete(messageType);
  }

  sendMessage(type: string, data?: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }));
    } else {
      console.warn('WebSocket não está conectado');
    }
  }

  calculateSimulation(state: SimulatorState) {
    this.sendMessage('calculate', { state });
  }

  ping() {
    this.sendMessage('ping', { timestamp: new Date().toISOString() });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}