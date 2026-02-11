# Quick Reference Guide

## Installation

```bash
# Install package
pip install -e .

# Install with dev dependencies
make install-dev
```

## Configuration

```yaml
# /etc/hetzner-vrrp/config.yaml
hetzner_api_token: "YOUR_API_TOKEN_HERE"

floating_ip_labels:
  role: vrrp
  cluster: production

alias_ips:
  - "10.0.0.100/32"
  - "10.0.0.101/32"

log_file: "/var/log/hetzner-vrrp-failover.log"
log_level: "INFO"
```

## CLI Commands

```bash
# Dry run - validate and preview changes (SAFE)
hetzner-vrrp-failover --dry-run

# Dry run with fake server ID (test locally without Hetzner server)
hetzner-vrrp-failover --dry-run --fake-server-id 12345

# Execute actual failover
hetzner-vrrp-failover

# Use custom config
hetzner-vrrp-failover -c /path/to/config.yaml

# Show help
hetzner-vrrp-failover --help

# Show version
hetzner-vrrp-failover --version
```

## VyOS Integration

```bash
configure
set high-availability vrrp group VRRP01 transition-script master '/usr/local/bin/hetzner-vrrp-failover -c /etc/hetzner-vrrp/config.yaml'
commit
save
```

## Development

```bash
# Run tests
make test

# Run tests with coverage
make coverage

# Run linters
make lint

# Format code
make format

# Clean build artifacts
make clean
```

## Python API

```python
from hetzner_vrrp_failover import HetznerFailover, Config

# Load configuration
config = Config('/path/to/config.yaml')

# Execute failover
failover = HetznerFailover(config)
success = failover.execute_failover()

# Dry run mode
failover = HetznerFailover(config, dry_run=True)
success = failover.execute_failover()  # Simulates without changes
```

## Dry-Run Mode

### CLI Validation
```bash
hetzner-vrrp-failover --dry-run
```
Output shows:
- Current server ID
- Floating IPs status (assigned/unassigned)
- What needs to be changed
- Summary of actions

### Programmatic Dry-Run
```python
failover = HetznerFailover(config, dry_run=True)
failover.execute_failover()
```
- Goes through entire failover process
- Logs all actions with `[DRY RUN]` prefix
- **Does NOT make any API changes**

## Troubleshooting

```bash
# Check logs
tail -f /var/log/hetzner-vrrp-failover.log

# Test configuration
hetzner-vrrp-failover --dry-run

# Verify metadata service
curl http://169.254.169.254/hetzner/v1/metadata/instance-id

# Check VRRP status (on VyOS)
show vrrp
```

## Common Issues

### "Config file not found"
- Check file path: `/etc/hetzner-vrrp/config.yaml`
- Use `-c` flag to specify custom location

### "Failed to get server ID from metadata service"
- Script must run on a Hetzner Cloud server
- Check network connectivity

### "No floating IPs found"
- Check labels in Hetzner Cloud Console
- Verify label configuration in config.yaml
- Labels must match exactly (case-sensitive)

## Security

```bash
# Set proper permissions on config file
sudo chmod 600 /etc/hetzner-vrrp/config.yaml
sudo chown root:root /etc/hetzner-vrrp/config.yaml
```

## File Locations

- Config: `/etc/hetzner-vrrp/config.yaml`
- Logs: `/var/log/hetzner-vrrp-failover.log`
- Binary: `/usr/local/bin/hetzner-vrrp-failover` (or in venv)

## Exit Codes

- `0` - Success
- `1` - Failure (configuration error, API error, etc.)
- `130` - Interrupted by user (Ctrl+C)

## Environment Variables

None required. All configuration via YAML file.

## Minimum Requirements

- Python 3.8+
- Hetzner Cloud server
- Valid Hetzner Cloud API token
- Network access to Hetzner Cloud API
