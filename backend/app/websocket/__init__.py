from typing import List, Dict, Set
from fastapi import WebSocket
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager for live updates"""
    
    def __init__(self):
        # Active connections by channel
        self.connections: Dict[str, Set[WebSocket]] = {
            "live-attendance": set(),
            "camera-status": set(),
            "system-status": set()
        }
        
    async def connect(self, websocket: WebSocket, channel: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        
        if channel not in self.connections:
            self.connections[channel] = set()
        
        self.connections[channel].add(websocket)
        logger.info(f"Client connected to {channel}")
        
    def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a WebSocket connection"""
        if channel in self.connections:
            self.connections[channel].discard(websocket)
            logger.info(f"Client disconnected from {channel}")
    
    async def broadcast(self, channel: str, message: dict):
        """
        Broadcast a message to all connections on a channel
        
        Args:
            channel: Channel name (live-attendance, camera-status, etc.)
            message: Message dict to send
        """
        if channel not in self.connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        disconnected = []
        
        for connection in self.connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.connections[channel].discard(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific client"""
        try:
            if "timestamp" not in message:
                message["timestamp"] = datetime.now(timezone.utc).isoformat()
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Personal WebSocket send error: {e}")
    
    def get_connection_count(self, channel: str = None) -> int:
        """Get number of active connections"""
        if channel:
            return len(self.connections.get(channel, set()))
        return sum(len(conns) for conns in self.connections.values())
    
    def get_all_channels(self) -> List[str]:
        """Get list of all channels"""
        return list(self.connections.keys())


# Global connection manager
websocket_manager = ConnectionManager()
