"""Command-line interface for Hetzner VRRP failover"""

import sys
import argparse
from typing import Optional

from . import __version__
from .config import Config
from .failover import HetznerFailover
from .exceptions import HetznerVRRPError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        prog='hetzner-vrrp-failover',
        description='Hetzner Cloud VRRP Failover Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute failover with default config
  %(prog)s
  
  # Execute failover with custom config
  %(prog)s -c /etc/hetzner/config.yaml
  
  # Dry run mode (check configuration only)
  %(prog)s --dry-run
  
  # Dry run with fake server ID (test without Hetzner server)
  %(prog)s --dry-run --fake-server-id 12345
  
  # Show version
  %(prog)s --version
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default=Config.DEFAULT_CONFIG_PATH,
        help=f'Path to configuration file (default: {Config.DEFAULT_CONFIG_PATH})'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration without making changes'
    )
    
    parser.add_argument(
        '--fake-server-id',
        type=int,
        metavar='ID',
        help='Fake server ID for testing (only works with --dry-run)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    return parser


def dry_run_validate(failover: HetznerFailover) -> int:
    """
    Validate configuration and show current state
    
    Args:
        failover: HetznerFailover instance
        
    Returns:
        Exit code (0 for success)
    """
    print("=" * 60)
    print("DRY RUN - Configuration Validation")
    print("=" * 60)
    print(f"Server ID: {failover.server_id}")
    print(f"Log level: {failover.config.log_level}")
    
    floating_ips = failover.get_floating_ips_by_labels()
    print(f"\nFound {len(floating_ips)} floating IP(s) matching labels:")
    
    needs_assignment = []
    if floating_ips:
        for fip in floating_ips:
            if fip.server:
                status = f"assigned to server {fip.server.id}"
                if fip.server.id == failover.server_id:
                    status += " ✓ (this server)"
                else:
                    status += " → needs reassignment"
                    needs_assignment.append(fip.ip)
            else:
                status = "unassigned → needs assignment"
                needs_assignment.append(fip.ip)
            print(f"  - {fip.ip} (ID: {fip.id}) - {status}")
    else:
        print("  (none)")
    
    alias_ips = failover.config.alias_ips
    print(f"\nConfigured alias IPs: {len(alias_ips)}")
    if alias_ips:
        for ip in alias_ips:
            print(f"  - {ip}")
    else:
        print("  (none)")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    if needs_assignment:
        print(f"⚠ {len(needs_assignment)} floating IP(s) need to be assigned")
        print("Run without --dry-run to execute failover")
    else:
        print("✓ All floating IPs already correctly assigned")
    
    return 0


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for CLI
    
    Args:
        argv: Optional command line arguments (for testing)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Validate --fake-server-id only works with --dry-run
    if args.fake_server_id and not args.dry_run:
        print("Error: --fake-server-id can only be used with --dry-run", file=sys.stderr)
        return 1
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Create metadata service (or fake it)
        if args.fake_server_id:
            from unittest.mock import Mock
            metadata_service = Mock()
            metadata_service.get_server_id.return_value = args.fake_server_id
            print(f"Using fake server ID: {args.fake_server_id}")
        else:
            metadata_service = None
        
        # Execute dry run or actual failover
        if args.dry_run:
            # Initialize in dry-run mode for validation only
            failover = HetznerFailover(config, metadata_service=metadata_service, dry_run=True)
            return dry_run_validate(failover)
        else:
            # Initialize and execute actual failover
            failover = HetznerFailover(config, metadata_service=metadata_service, dry_run=False)
            success = failover.execute_failover()
            return 0 if success else 1
            
    except HetznerVRRPError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
