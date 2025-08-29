"""Socket client for LG Air Conditioner."""
import asyncio
import logging
import socket
import binascii
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class LGSocketClient:
    """Socket client for LG Air Conditioner."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the socket client."""
        self.host = host
        self.port = port
        self._socket = None
        self._lock = asyncio.Lock()

    async def async_send_command(self, packet: str) -> Optional[str]:
        """Send command and receive response."""
        async with self._lock:
            try:
                # Convert hex string to bytes
                packet_bytes = bytes.fromhex(packet)
                
                # Create socket and connect
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=5.0
                )
                
                try:
                    # Send packet
                    writer.write(packet_bytes)
                    await writer.drain()
                    
                    # Receive response
                    response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
                    
                    if response:
                        hex_response = binascii.hexlify(response).decode()
                        _LOGGER.debug("Received response: %s", hex_response)
                        return hex_response
                    else:
                        _LOGGER.warning("No response received")
                        return None
                        
                finally:
                    writer.close()
                    await writer.wait_closed()
                    
            except asyncio.TimeoutError:
                _LOGGER.error("Socket operation timed out")
                return None
            except Exception as err:
                _LOGGER.error("Socket error: %s", err)
                return None

    async def async_close(self) -> None:
        """Close the socket connection."""
        # No persistent connection to close in this implementation
        pass
