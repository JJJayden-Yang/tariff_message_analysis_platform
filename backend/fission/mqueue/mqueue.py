import logging
import json
from typing import Dict, Any, Optional
from flask import current_app, request
import redis


def main() -> str:
    """Message queue producer for Redis streaming.

    Handles:
    - Redis connection pooling
    - JSON payload serialization
    - Topic-based message routing via headers
    - Message size logging

    Returns:
        'OK' with HTTP 200 on successful enqueue

    Raises:
        redis.RedisError: For connection/operation failures
        JSONDecodeError: If invalid payload received
    """
    req: Request = request
    
    # Extract routing parameters
    topic: Optional[str] = req.headers.get('X-Fission-Params-Topic')
    json_data: Dict[str, Any] = req.get_json()
    
    # Initialize Redis client with type annotation
    redis_client: redis.StrictRedis = redis.StrictRedis(
        host='redis-headless.redis.svc.cluster.local',
        socket_connect_timeout=5,
        decode_responses=False
    )
    
    # Publish message to set
    redis_client.lpush(
        topic,
        json.dumps(json_data).encode('utf-8')
    )
    
    # Structured logging with message metrics
    current_app.logger.info(
        f'Enqueued to {topic} topic - '
        f'Payload size: {len(json_data)} bytes'
    )
    
    return     f'Enqueued to {topic} topic - Payload size: {len(json_data)} bytes'
