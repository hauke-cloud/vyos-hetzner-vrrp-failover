"""Configuration management for Hetzner VRRP failover"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .exceptions import ConfigError


class Config:
    """Configuration manager for Hetzner VRRP failover"""
    
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_CONFIG_PATH = "/etc/hetzner-vrrp/config.yaml"
    REQUIRED_FIELDS = ["hetzner_api_token"]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from file
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            ConfigError: If configuration is invalid or missing
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config = self._load_config()
        self._validate()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")
            
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                
            if config is None:
                raise ConfigError("Config file is empty")
                
            return config
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read config file: {e}")
            
    def _validate(self):
        """Validate required configuration fields"""
        for field in self.REQUIRED_FIELDS:
            if not self._config.get(field):
                raise ConfigError(f"Required field '{field}' missing in config")
                
        # Validate log level if provided
        log_level = self._config.get('log_level', self.DEFAULT_LOG_LEVEL)
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level.upper() not in valid_levels:
            raise ConfigError(
                f"Invalid log_level '{log_level}'. Must be one of: {', '.join(valid_levels)}"
            )
    
    @property
    def api_token(self) -> str:
        """Get Hetzner Cloud API token"""
        return self._config['hetzner_api_token']
    
    @property
    def floating_ip_labels(self) -> Dict[str, str]:
        """Get floating IP label filters"""
        return self._config.get('floating_ip_labels', {})
    
    @property
    def alias_ips(self) -> List[str]:
        """Get list of alias IPs to configure"""
        return self._config.get('alias_ips', [])
    
    @property
    def log_file(self) -> Optional[str]:
        """Get log file path"""
        return self._config.get('log_file')
    
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self._config.get('log_level', self.DEFAULT_LOG_LEVEL).upper()
    
    def to_dict(self) -> Dict:
        """Export configuration as dictionary (excluding sensitive data)"""
        return {
            'floating_ip_labels': self.floating_ip_labels,
            'alias_ips': self.alias_ips,
            'log_file': self.log_file,
            'log_level': self.log_level,
            'has_api_token': bool(self.api_token),
        }
