"""Hetzner Cloud metadata service client"""

import requests
from typing import Optional
from .exceptions import MetadataError


class MetadataService:
    """Client for Hetzner Cloud metadata service"""
    
    METADATA_BASE_URL = "http://169.254.169.254/hetzner/v1/metadata"
    DEFAULT_TIMEOUT = 5
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize metadata service client
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    def get_server_id(self) -> int:
        """
        Get the current server ID from metadata service
        
        Returns:
            Server ID as integer
            
        Raises:
            MetadataError: If metadata service is unavailable or returns invalid data
        """
        try:
            response = requests.get(
                f"{self.METADATA_BASE_URL}/instance-id",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            server_id_str = response.text.strip()
            server_id = int(server_id_str)
            
            return server_id
            
        except requests.exceptions.Timeout:
            raise MetadataError(
                "Timeout connecting to metadata service. "
                "Are you running this on a Hetzner Cloud server?"
            )
        except requests.exceptions.RequestException as e:
            raise MetadataError(f"Failed to connect to metadata service: {e}")
        except ValueError:
            raise MetadataError(f"Invalid server ID from metadata service: {server_id_str}")
    
    def get_hostname(self) -> Optional[str]:
        """
        Get the server hostname from metadata service
        
        Returns:
            Hostname string or None if not available
        """
        try:
            response = requests.get(
                f"{self.METADATA_BASE_URL}/hostname",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.text.strip()
        except Exception:
            return None
