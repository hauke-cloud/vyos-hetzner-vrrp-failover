"""Tests for CLI module"""

import pytest
from unittest.mock import patch, Mock

from hetzner_vrrp_failover.cli import main, create_parser


class TestCLI:
    """Test suite for CLI functionality"""
    
    def test_parser_creation(self):
        """Test argument parser creation"""
        parser = create_parser()
        
        # Test default arguments
        args = parser.parse_args([])
        assert args.config == '/etc/hetzner-vrrp/config.yaml'
        assert args.dry_run is False
    
    def test_parser_with_config(self):
        """Test parser with custom config"""
        parser = create_parser()
        args = parser.parse_args(['-c', '/custom/path.yaml'])
        
        assert args.config == '/custom/path.yaml'
    
    def test_parser_dry_run(self):
        """Test parser with dry-run flag"""
        parser = create_parser()
        args = parser.parse_args(['--dry-run'])
        
        assert args.dry_run is True
    
    @patch('hetzner_vrrp_failover.cli.HetznerFailover')
    @patch('hetzner_vrrp_failover.cli.Config')
    def test_main_success(self, mock_config, mock_failover, tmp_path):
        """Test successful main execution"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("hetzner_api_token: test")
        
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_failover_instance = Mock()
        mock_failover_instance.execute_failover.return_value = True
        mock_failover.return_value = mock_failover_instance
        
        exit_code = main(['-c', str(config_file)])
        
        assert exit_code == 0
        mock_failover_instance.execute_failover.assert_called_once()
    
    @patch('hetzner_vrrp_failover.cli.HetznerFailover')
    @patch('hetzner_vrrp_failover.cli.Config')
    def test_main_failure(self, mock_config, mock_failover, tmp_path):
        """Test main execution with failover failure"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("hetzner_api_token: test")
        
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_failover_instance = Mock()
        mock_failover_instance.execute_failover.return_value = False
        mock_failover.return_value = mock_failover_instance
        
        exit_code = main(['-c', str(config_file)])
        
        assert exit_code == 1
    
    @patch('hetzner_vrrp_failover.cli.HetznerFailover')
    @patch('hetzner_vrrp_failover.cli.Config')
    def test_main_dry_run(self, mock_config, mock_failover, tmp_path, capsys):
        """Test main execution in dry-run mode"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("hetzner_api_token: test")
        
        mock_config_instance = Mock()
        mock_config_instance.log_level = "INFO"
        mock_config_instance.alias_ips = ["10.0.0.100/32"]
        mock_config.return_value = mock_config_instance
        
        mock_fip = Mock()
        mock_fip.id = 1
        mock_fip.ip = "1.2.3.4"
        mock_fip.server = None
        
        mock_failover_instance = Mock()
        mock_failover_instance.server_id = 12345
        mock_failover_instance.config = mock_config_instance
        mock_failover_instance.get_floating_ips_by_labels.return_value = [mock_fip]
        mock_failover.return_value = mock_failover_instance
        
        exit_code = main(['-c', str(config_file), '--dry-run'])
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "DRY RUN - Configuration Validation" in captured.out
        assert "12345" in captured.out
        assert "1.2.3.4" in captured.out
    
    def test_main_config_error(self):
        """Test main with configuration error"""
        exit_code = main(['-c', '/nonexistent/config.yaml'])
        
        assert exit_code == 1
    
    @patch('hetzner_vrrp_failover.cli.HetznerFailover')
    @patch('hetzner_vrrp_failover.cli.Config')
    def test_fake_server_id(self, mock_config, mock_failover, tmp_path, capsys):
        """Test fake server ID with dry-run"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("hetzner_api_token: test")
        
        mock_config_instance = Mock()
        mock_config_instance.log_level = "INFO"
        mock_config_instance.alias_ips = []
        mock_config.return_value = mock_config_instance
        
        mock_failover_instance = Mock()
        mock_failover_instance.server_id = 99999
        mock_failover_instance.config = mock_config_instance
        mock_failover_instance.get_floating_ips_by_labels.return_value = []
        mock_failover.return_value = mock_failover_instance
        
        exit_code = main(['-c', str(config_file), '--dry-run', '--fake-server-id', '99999'])
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Using fake server ID: 99999" in captured.out
        assert "99999" in captured.out
    
    def test_fake_server_id_without_dry_run(self, capsys):
        """Test that fake server ID requires dry-run"""
        exit_code = main(['--fake-server-id', '12345'])
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "--fake-server-id can only be used with --dry-run" in captured.err
