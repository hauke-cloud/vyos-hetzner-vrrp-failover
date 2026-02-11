"""Custom exceptions for Hetzner VRRP failover"""


class HetznerVRRPError(Exception):
    """Base exception for Hetzner VRRP failover errors"""
    pass


class HetznerAPIError(HetznerVRRPError):
    """Exception raised for Hetzner API errors"""
    pass


class ConfigError(HetznerVRRPError):
    """Exception raised for configuration errors"""
    pass


class MetadataError(HetznerVRRPError):
    """Exception raised for metadata service errors"""
    pass
