import time
import asyncio
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket

class FlashTestSession:
    def __init__(self, token: str, total_seconds: int = 60):
        self.token = token
        self.total_seconds = total_seconds
        self.start_time: Optional[float] = None
        self.is_active = False
        self.is_completed = False
        self.answers: Dict[str, str] = {}
        self.sockets: Set[WebSocket] = set()
        self.timer_task: Optional[asyncio.Task] = None
        self.disconnect_time: Optional[float] = None

    @property
    def elapsed_seconds(self) -> int:
        if not self.start_time:
            return 0
        return int(time.time() - self.start_time)

    @property
    def remaining_seconds(self) -> int:
        remaining = self.total_seconds - self.elapsed_seconds
        return max(0, remaining)

class WebSocketManager:
    """
    Manages active Flash Test WebSockets, real-time timer broadcasts and reconnection (RF-011, RNF-001, RNF-008)
    """
    def __init__(self):
        # Map token -> FlashTestSession
        self.sessions: Dict[str, FlashTestSession] = {}
        # Teacher dashboard observers: course_id -> Set[WebSocket]
        self.teacher_dashboards: Dict[int, Set[WebSocket]] = {}

    def get_or_create_session(self, token: str, total_seconds: int = 60) -> FlashTestSession:
        if token not in self.sessions:
            self.sessions[token] = FlashTestSession(token, total_seconds)
        return self.sessions[token]

    async def connect_student(self, websocket: WebSocket, token: str, total_seconds: int = 60) -> FlashTestSession:
        await websocket.accept()
        session = self.get_or_create_session(token, total_seconds)
        session.sockets.add(websocket)
        session.disconnect_time = None
        return session

    def disconnect_student(self, websocket: WebSocket, token: str):
        if token in self.sessions:
            session = self.sessions[token]
            session.sockets.discard(websocket)
            if not session.sockets:
                session.disconnect_time = time.time()

    async def broadcast_to_session(self, token: str, message: dict):
        if token in self.sessions:
            dead_sockets = set()
            for ws in self.sessions[token].sockets:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self.sessions[token].sockets.discard(ws)

    # Teacher dashboard live subscription
    async def connect_teacher(self, websocket: WebSocket, course_id: int):
        await websocket.accept()
        if course_id not in self.teacher_dashboards:
            self.teacher_dashboards[course_id] = set()
        self.teacher_dashboards[course_id].add(websocket)

    def disconnect_teacher(self, websocket: WebSocket, course_id: int):
        if course_id in self.teacher_dashboards:
            self.teacher_dashboards[course_id].discard(websocket)

    async def notify_teacher_dashboard(self, course_id: int, message: dict):
        if course_id in self.teacher_dashboards:
            dead = set()
            for ws in self.teacher_dashboards[course_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.teacher_dashboards[course_id].discard(ws)

ws_manager = WebSocketManager()
