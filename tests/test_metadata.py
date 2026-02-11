"""Tests for metadata service module"""

import pytest
import responses
from requests.exceptions import Timeout

from hetzner_vrrp_failover.metadata import MetadataService
from hetzner_vrrp_failover.exceptions import MetadataError


class TestMetadataService:
    """Test suite for MetadataService class"""
    
    @responses.activate
    def test_get_server_id_success(self):
        """Test successful server ID retrieval"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/instance-id",
            body="12345",
            status=200
        )
        
        service = MetadataService()
        server_id = service.get_server_id()
        
        assert server_id == 12345
    
    @responses.activate
    def test_get_server_id_with_whitespace(self):
        """Test server ID retrieval with whitespace"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/instance-id",
            body="  67890  \n",
            status=200
        )
        
        service = MetadataService()
        server_id = service.get_server_id()
        
        assert server_id == 67890
    
    @responses.activate
    def test_get_server_id_timeout(self):
        """Test timeout handling"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/instance-id",
            body=Timeout()
        )
        
        service = MetadataService(timeout=1)
        
        with pytest.raises(MetadataError, match="Timeout connecting"):
            service.get_server_id()
    
    @responses.activate
    def test_get_server_id_invalid_response(self):
        """Test invalid server ID response"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/instance-id",
            body="not_a_number",
            status=200
        )
        
        service = MetadataService()
        
        with pytest.raises(MetadataError, match="Invalid server ID"):
            service.get_server_id()
    
    @responses.activate
    def test_get_server_id_http_error(self):
        """Test HTTP error handling"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/instance-id",
            status=500
        )
        
        service = MetadataService()
        
        with pytest.raises(MetadataError, match="Failed to connect"):
            service.get_server_id()
    
    @responses.activate
    def test_get_hostname_success(self):
        """Test successful hostname retrieval"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/hostname",
            body="test-server",
            status=200
        )
        
        service = MetadataService()
        hostname = service.get_hostname()
        
        assert hostname == "test-server"
    
    @responses.activate
    def test_get_hostname_failure(self):
        """Test hostname retrieval failure returns None"""
        responses.add(
            responses.GET,
            "http://169.254.169.254/hetzner/v1/metadata/hostname",
            status=500
        )
        
        service = MetadataService()
        hostname = service.get_hostname()
        
        assert hostname is None
