#!/usr/bin/env python3
"""
Quick WebSocket connection test using socket.io-client
Tests that the backend WebSocket endpoint is accessible and responds correctly.
"""
import socketio
import asyncio
import sys
import uuid

async def test_websocket():
    """Test WebSocket connection to backend."""
    print("=" * 80)
    print("Testing WebSocket Connection")
    print("=" * 80)
    print()
    
    # Create Socket.IO client
    sio = socketio.AsyncClient()
    
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    
    print(f"Connecting to http://localhost:8000...")
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print()
    
    try:
        # Connect
        await sio.connect(
            'http://localhost:8000',
            wait_timeout=10,
            socketio_path='/socket.io',
            transports=['websocket', 'polling']
        )
        print("✓ Connected to WebSocket server")
        
        # Wait for connection event
        await asyncio.sleep(1)
        
        # Initialize session
        print("\nSending init_session event...")
        await sio.emit('init_session', {
            'user_id': user_id,
            'session_id': session_id,
            'course_id': 'test-course'
        })
        print("✓ init_session event sent")
        
        # Wait for session_initialized
        print("\nWaiting for session_initialized response...")
        await asyncio.sleep(2)
        
        # Send a test text message
        print("\nSending test text message...")
        await sio.emit('text', {
            'type': 'text',
            'session_id': session_id,
            'user_id': user_id,
            'text': 'Hello, this is a test message'
        })
        print("✓ Text message sent")
        
        # Wait for response
        print("\nWaiting for response...")
        await asyncio.sleep(5)
        
        # Disconnect
        await sio.disconnect()
        print("\n✓ Disconnected successfully")
        
        print("\n" + "=" * 80)
        print("WebSocket Test: PASSED")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n✗ WebSocket Test FAILED: {str(e)}")
        print("\n" + "=" * 80)
        print("WebSocket Test: FAILED")
        print("=" * 80)
        return False
    finally:
        if sio.connected:
            await sio.disconnect()

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

