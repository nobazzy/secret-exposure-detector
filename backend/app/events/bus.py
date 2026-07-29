import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    name: str
    payload: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    async def publish(self, event: Event):
        if event.name in self._subscribers:
            for handler in self._subscribers[event.name]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)

# Global EventBus instance
bus = EventBus()
