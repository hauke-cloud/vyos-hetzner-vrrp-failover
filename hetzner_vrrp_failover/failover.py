"""Main failover logic for Hetzner VRRP"""

import logging
from typing import List, Optional
from hcloud import Client
from hcloud.floating_ips.domain import FloatingIP
from hcloud.servers.domain import Server

from .config import Config
from .metadata import MetadataService
from .logger import setup_logger
from .exceptions import HetznerAPIError


class HetznerFailover:
    """Manages Hetzner Cloud floating IPs and alias IPs for VRRP failover"""

    def __init__(
        self,
        config: Config,
        metadata_service: Optional[MetadataService] = None,
        logger: Optional[logging.Logger] = None,
        dry_run: bool = False,
    ):
        """
        Initialize failover manager

        Args:
            config: Configuration object
            metadata_service: Optional metadata service (for testing)
            logger: Optional logger instance (for testing)
            dry_run: If True, only simulate actions without making changes
        """
        self.config = config
        self.client = Client(token=config.api_token)
        self.metadata_service = metadata_service or MetadataService()
        self.logger = logger or setup_logger(
            __name__, log_level=config.log_level, log_file=config.log_file
        )
        self.dry_run = dry_run

        self.server_id = self.metadata_service.get_server_id()
        self.logger.info(f"Initialized for server ID: {self.server_id}")
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No changes will be made")
        self._server = None

    @property
    def server(self) -> Server:
        """Get the server object (cached)"""
        if self._server is None:
            try:
                self._server = self.client.servers.get_by_id(self.server_id)
                if self._server is None:
                    raise HetznerAPIError(f"Server with ID {self.server_id} not found")
            except Exception as e:
                raise HetznerAPIError(f"Failed to get server: {e}")
        return self._server

    def get_floating_ips_by_labels(self) -> List[FloatingIP]:
        """
        Get floating IPs matching configured labels

        Returns:
            List of FloatingIP objects

        Raises:
            HetznerAPIError: If API request fails
        """
        labels = self.config.floating_ip_labels

        if not labels:
            self.logger.warning("No floating_ip_labels configured")
            return []

        self.logger.info(f"Fetching floating IPs with labels: {labels}")

        try:
            floating_ips = self.client.floating_ips.get_all(label_selector=labels)
            self.logger.info(f"Found {len(floating_ips)} floating IPs matching labels")
            return floating_ips
        except Exception as e:
            raise HetznerAPIError(f"Failed to get floating IPs: {e}")

    def assign_floating_ip(self, floating_ip: FloatingIP) -> bool:
        """
        Assign a floating IP to this server

        Args:
            floating_ip: FloatingIP object to assign

        Returns:
            True if successful, False otherwise
        """
        try:
            ip_address = floating_ip.ip

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would assign floating IP {ip_address} (ID: {floating_ip.id}) "
                    f"to server {self.server_id}"
                )
                return True

            self.logger.info(
                f"Assigning floating IP {ip_address} (ID: {floating_ip.id}) "
                f"to server {self.server_id}"
            )

            floating_ip.assign(self.server)
            self.logger.info(f"Successfully assigned floating IP {ip_address}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to assign floating IP {floating_ip.ip}: {e}")
            return False

    def assign_all_floating_ips(self) -> bool:
        """
        Assign all configured floating IPs to this server

        Returns:
            True if all assignments successful, False otherwise
        """
        floating_ips = self.get_floating_ips_by_labels()

        if not floating_ips:
            self.logger.warning("No floating IPs found to assign")
            return True

        success = True
        for fip in floating_ips:
            # Check if already assigned to this server
            if fip.server and fip.server.id == self.server_id:
                msg = f"Floating IP {fip.ip} already assigned to this server"
                if self.dry_run:
                    self.logger.info(f"[DRY RUN] {msg}")
                else:
                    self.logger.info(msg)
                continue

            if not self.assign_floating_ip(fip):
                success = False

        return success

    def assign_alias_ips(self) -> bool:
        """
        Assign alias IPs to this server

        Returns:
            True if successful, False otherwise
        """
        alias_ips = self.config.alias_ips

        if not alias_ips:
            self.logger.info("No alias IPs configured")
            return True

        if self.dry_run:
            self.logger.info(
                f"[DRY RUN] Would assign {len(alias_ips)} alias IP(s) to server {self.server_id}"
            )
        else:
            self.logger.info(
                f"Assigning {len(alias_ips)} alias IP(s) to server {self.server_id}"
            )

        try:
            import ipaddress

            server = self.server

            # Alias IPs in Hetzner are assigned to private networks, not public IPs
            # We need to find which network each alias IP belongs to
            if not server.private_net:
                self.logger.error(
                    "No private networks attached to server - alias IPs require a private network"
                )
                return False

            # Group alias IPs by network
            network_aliases = {}  # network_id -> list of alias IPs
            unmatched_aliases = []

            for alias_ip in alias_ips:
                matched = False
                # Find which network this alias belongs to
                for pnet in server.private_net:
                    # Get the network's IP range to check if alias belongs to it
                    # We can infer from the server's IP on that network
                    server_ip = ipaddress.ip_address(pnet.ip)
                    alias_addr = ipaddress.ip_address(alias_ip)

                    # Check if both IPs are in same class (both v4 or both v6)
                    if server_ip.version == alias_addr.version:
                        # For IPv4, check if they're in same /24 (common private network setup)
                        # For more accurate matching, we'd need to query the network details
                        # But for now, match by IP prefix similarity
                        if server_ip.version == 4:
                            # Match first 3 octets (assumes /24 or smaller subnet)
                            server_prefix = ".".join(pnet.ip.split(".")[:-1])
                            alias_prefix = ".".join(alias_ip.split(".")[:-1])
                            if server_prefix == alias_prefix:
                                network_aliases.setdefault(pnet.network, []).append(
                                    alias_ip
                                )
                                matched = True
                                break
                        else:  # IPv6
                            # Match first 64 bits
                            if str(server_ip)[:19] == str(alias_addr)[:19]:
                                network_aliases.setdefault(pnet.network, []).append(
                                    alias_ip
                                )
                                matched = True
                                break

                if not matched:
                    unmatched_aliases.append(alias_ip)

            if unmatched_aliases:
                self.logger.warning(
                    f"Could not match alias IPs to networks: {', '.join(unmatched_aliases)}"
                )

            if not network_aliases:
                self.logger.error(
                    "No alias IPs could be matched to server's private networks"
                )
                return False

            # Assign aliases to each network
            for network, aliases_to_add in network_aliases.items():
                # Get current aliases for this network
                current_aliases = []
                for pnet in server.private_net:
                    if pnet.network == network:
                        current_aliases = pnet.alias_ips or []
                        break

                # Merge current and new aliases
                all_aliases = list(set(current_aliases + aliases_to_add))
                new_aliases = set(all_aliases) - set(current_aliases)

                if self.dry_run:
                    if new_aliases:
                        self.logger.info(
                            f"[DRY RUN] Would add aliases {', '.join(new_aliases)} to network {network}"
                        )
                    else:
                        self.logger.info(
                            f"[DRY RUN] Aliases already configured on network {network}"
                        )
                    continue

                # Use change_alias_ips for network alias IPs
                self.logger.info(
                    f"Assigning {len(aliases_to_add)} alias IP(s) to network {network}"
                )
                self.client.servers.change_alias_ips(server, network, all_aliases)
                self.logger.info(
                    f"Successfully assigned aliases to network: {', '.join(aliases_to_add)}"
                )

            return True

        except Exception as e:
            self.logger.error(f"Failed to assign alias IPs: {e}")
            import traceback

            self.logger.debug(traceback.format_exc())
            return False

    def execute_failover(self) -> bool:
        """
        Execute complete failover process

        Returns:
            True if all operations successful, False otherwise
        """
        self.logger.info("=" * 60)
        if self.dry_run:
            self.logger.info("Starting VRRP failover process (DRY RUN)")
        else:
            self.logger.info("Starting VRRP failover process")
        self.logger.info("=" * 60)

        floating_success = self.assign_all_floating_ips()
        alias_success = self.assign_alias_ips()

        if floating_success and alias_success:
            self.logger.info("=" * 60)
            if self.dry_run:
                self.logger.info(
                    "Failover dry run completed successfully (no changes made)"
                )
            else:
                self.logger.info("Failover completed successfully")
            self.logger.info("=" * 60)
            return True
        else:
            self.logger.error("=" * 60)
            if self.dry_run:
                self.logger.error("Failover dry run completed with errors")
            else:
                self.logger.error("Failover completed with errors")
            self.logger.error("=" * 60)
            return False
