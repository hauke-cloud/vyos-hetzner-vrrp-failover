"""Tests for configuration module"""

import pytest
import tempfile
from pathlib import Path

from hetzner_vrrp_failover.config import Config
from hetzner_vrrp_failover.exceptions import ConfigError


class TestConfig:
    """Test suite for Config class"""
    
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
hetzner_api_token: test_token_123
floating_ip_labels:
  role: vrrp
  cluster: prod
alias_ips:
  - 10.0.0.100/32
  - 10.0.0.101/32
log_level: DEBUG
log_file: /var/log/test.log
        """)
        
        config = Config(str(config_file))
        
        assert config.api_token == "test_token_123"
        assert config.floating_ip_labels == {"role": "vrrp", "cluster": "prod"}
        assert config.alias_ips == ["10.0.0.100/32", "10.0.0.101/32"]
        assert config.log_level == "DEBUG"
        assert config.log_file == "/var/log/test.log"
    
    def test_minimal_config(self, tmp_path):
        """Test loading minimal valid configuration"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("hetzner_api_token: test_token")
        
        config = Config(str(config_file))
        
        assert config.api_token == "test_token"
        assert config.floating_ip_labels == {}
        assert config.alias_ips == []
        assert config.log_level == "INFO"
        assert config.log_file is None
    
    def test_missing_api_token(self, tmp_path):
        """Test that missing API token raises error"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("floating_ip_labels:\n  role: vrrp")
        
        with pytest.raises(ConfigError, match="Required field 'hetzner_api_token'"):
            Config(str(config_file))
    
    def test_file_not_found(self):
        """Test that non-existent file raises error"""
        with pytest.raises(ConfigError, match="Config file not found"):
            Config("/nonexistent/path/config.yaml")
    
    def test_invalid_yaml(self, tmp_path):
        """Test that invalid YAML raises error"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigError, match="Invalid YAML"):
            Config(str(config_file))
    
    def test_empty_config(self, tmp_path):
        """Test that empty config file raises error"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        
        with pytest.raises(ConfigError, match="Config file is empty"):
            Config(str(config_file))
    
    def test_invalid_log_level(self, tmp_path):
        """Test that invalid log level raises error"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
hetzner_api_token: test_token
log_level: INVALID
        """)
        
        with pytest.raises(ConfigError, match="Invalid log_level"):
            Config(str(config_file))
    
    def test_to_dict(self, tmp_path):
        """Test configuration export to dictionary"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
hetzner_api_token: secret_token
floating_ip_labels:
  role: vrrp
alias_ips:
  - 10.0.0.100/32
        """)
        
        config = Config(str(config_file))
        config_dict = config.to_dict()
        
        assert config_dict['has_api_token'] is True
        assert config_dict['floating_ip_labels'] == {"role": "vrrp"}
        assert config_dict['alias_ips'] == ["10.0.0.100/32"]
        # Ensure API token is not exposed
        assert 'hetzner_api_token' not in config_dict
        assert 'secret_token' not in str(config_dict)
