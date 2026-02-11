"""Tests for failover module"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import logging

from hetzner_vrrp_failover.failover import HetznerFailover
from hetzner_vrrp_failover.config import Config
from hetzner_vrrp_failover.metadata import MetadataService
from hetzner_vrrp_failover.exceptions import HetznerAPIError


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
hetzner_api_token: test_token
floating_ip_labels:
  role: vrrp
alias_ips:
  - 10.0.0.100/32
    """)
    return Config(str(config_file))


@pytest.fixture
def mock_metadata():
    """Create a mock metadata service"""
    metadata = Mock(spec=MetadataService)
    metadata.get_server_id.return_value = 12345
    return metadata


@pytest.fixture
def mock_logger():
    """Create a mock logger"""
    return Mock(spec=logging.Logger)


class TestHetznerFailover:
    """Test suite for HetznerFailover class"""
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_initialization(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test failover manager initialization"""
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        
        assert failover.server_id == 12345
        assert failover.config == mock_config
        assert failover.dry_run is False
        mock_metadata.get_server_id.assert_called_once()
        mock_client.assert_called_once_with(token="test_token")
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_initialization_dry_run(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test failover manager initialization in dry-run mode"""
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger, dry_run=True)
        
        assert failover.server_id == 12345
        assert failover.dry_run is True
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_get_floating_ips_empty_labels(self, mock_client, tmp_path, mock_metadata, mock_logger):
        """Test getting floating IPs with no labels configured"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("hetzner_api_token: test_token")
        config = Config(str(config_file))
        
        failover = HetznerFailover(config, mock_metadata, mock_logger)
        result = failover.get_floating_ips_by_labels()
        
        assert result == []
        mock_logger.warning.assert_called_once()
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_get_floating_ips_success(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test successful floating IP retrieval"""
        mock_fip1 = Mock()
        mock_fip1.id = 1
        mock_fip1.ip = "1.2.3.4"
        
        mock_fip2 = Mock()
        mock_fip2.id = 2
        mock_fip2.ip = "5.6.7.8"
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.floating_ips.get_all.return_value = [mock_fip1, mock_fip2]
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.get_floating_ips_by_labels()
        
        assert len(result) == 2
        assert result[0].ip == "1.2.3.4"
        assert result[1].ip == "5.6.7.8"
        mock_client_instance.floating_ips.get_all.assert_called_once()
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_assign_floating_ip_success(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test successful floating IP assignment"""
        mock_fip = Mock()
        mock_fip.id = 1
        mock_fip.ip = "1.2.3.4"
        mock_fip.assign = Mock()
        
        mock_server = Mock()
        mock_server.id = 12345
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.servers.get_by_id.return_value = mock_server
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.assign_floating_ip(mock_fip)
        
        assert result is True
        mock_fip.assign.assert_called_once_with(mock_server)
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_assign_floating_ip_dry_run(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test floating IP assignment in dry-run mode"""
        mock_fip = Mock()
        mock_fip.id = 1
        mock_fip.ip = "1.2.3.4"
        mock_fip.assign = Mock()
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger, dry_run=True)
        result = failover.assign_floating_ip(mock_fip)
        
        assert result is True
        # Should not call assign in dry-run mode
        mock_fip.assign.assert_not_called()
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_assign_floating_ip_failure(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test floating IP assignment failure"""
        mock_fip = Mock()
        mock_fip.id = 1
        mock_fip.ip = "1.2.3.4"
        mock_fip.assign = Mock(side_effect=Exception("API Error"))
        
        mock_server = Mock()
        mock_client_instance = mock_client.return_value
        mock_client_instance.servers.get_by_id.return_value = mock_server
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.assign_floating_ip(mock_fip)
        
        assert result is False
        mock_logger.error.assert_called()
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_assign_all_floating_ips_already_assigned(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test that already assigned IPs are skipped"""
        mock_fip = Mock()
        mock_fip.id = 1
        mock_fip.ip = "1.2.3.4"
        mock_fip.server = Mock()
        mock_fip.server.id = 12345  # Same as our server
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.floating_ips.get_all.return_value = [mock_fip]
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.assign_all_floating_ips()
        
        assert result is True
        # Should not call assign since it's already assigned
        assert not mock_fip.assign.called
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_assign_alias_ips_success(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test successful alias IP assignment"""
        mock_server = Mock()
        mock_server.id = 12345
        mock_server.public_net.ipv4.alias_ips = []
        mock_server.public_net.ipv6.alias_ips = []
        mock_server.update = Mock()
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.servers.get_by_id.return_value = mock_server
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.assign_alias_ips()
        
        assert result is True
        mock_server.update.assert_called_once()
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_assign_alias_ips_dry_run(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test alias IP assignment in dry-run mode"""
        mock_server = Mock()
        mock_server.id = 12345
        mock_server.public_net.ipv4.alias_ips = []
        mock_server.public_net.ipv6.alias_ips = []
        mock_server.update = Mock()
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.servers.get_by_id.return_value = mock_server
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger, dry_run=True)
        result = failover.assign_alias_ips()
        
        assert result is True
        # Should not call update in dry-run mode
        mock_server.update.assert_not_called()
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_execute_failover_success(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test successful complete failover"""
        mock_server = Mock()
        mock_server.id = 12345
        mock_server.public_net.ipv4.alias_ips = []
        mock_server.public_net.ipv6.alias_ips = []
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.servers.get_by_id.return_value = mock_server
        mock_client_instance.floating_ips.get_all.return_value = []
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.execute_failover()
        
        assert result is True
    
    @patch('hetzner_vrrp_failover.failover.Client')
    def test_execute_failover_partial_failure(self, mock_client, mock_config, mock_metadata, mock_logger):
        """Test failover with partial failures"""
        mock_server = Mock()
        mock_server.public_net.ipv4.alias_ips = []
        mock_server.update = Mock(side_effect=Exception("Update failed"))
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.servers.get_by_id.return_value = mock_server
        mock_client_instance.floating_ips.get_all.return_value = []
        
        failover = HetznerFailover(mock_config, mock_metadata, mock_logger)
        result = failover.execute_failover()
        
        assert result is False
        mock_logger.error.assert_called()
