import { useState, useEffect, useCallback, useRef } from 'react';

interface WebSocketMessage {
  event: string;
  [key: string]: any;
}

export function useWebSocket(channel: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${channel}`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log(`WebSocket connected to ${channel}`);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
      setMessages((prev) => [message, ...prev].slice(0, 100)); // Keep last 100 messages
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log(`WebSocket disconnected from ${channel}`);
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    wsRef.current = ws;
  }, [channel]);

  useEffect(() => {
    connect();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return {
    isConnected,
    lastMessage,
    messages,
    sendMessage,
  };
}
