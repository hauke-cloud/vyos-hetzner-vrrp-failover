"""
Hetzner Cloud VRRP Failover Package

A Python package to automatically manage Hetzner Cloud floating IPs 
and alias IPs during VyOS VRRP failovers.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .failover import HetznerFailover
from .config import Config
from .exceptions import HetznerAPIError, ConfigError

__all__ = [
    "HetznerFailover",
    "Config",
    "HetznerAPIError",
    "ConfigError",
]
