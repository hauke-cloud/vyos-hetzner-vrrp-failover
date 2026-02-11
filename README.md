# Hetzner Cloud VRRP Failover Script for VyOS

A modular Python package to automatically manage Hetzner Cloud floating IPs and alias IPs during VyOS VRRP failovers.

## Features

- **Floating IP Management**: Automatically assigns floating IPs matching configured labels to the active VRRP node
- **Alias IP Management**: Configures alias IPs on the active server
- **VyOS Integration**: Designed to be called from VyOS VRRP transition scripts
- **Configurable**: YAML-based configuration for easy management
- **Logging**: Comprehensive logging for debugging and monitoring

## Prerequisites

- Python 3.6+
- Hetzner Cloud API token
- VyOS router with VRRP configured
- Server running in Hetzner Cloud

## Installation

### Option 1: Install from source (recommended for development)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hetzner-vrrp-failover.git
cd hetzner-vrrp-failover
```

2. Install the package:
```bash
# For production
pip3 install -e .

# For development (includes testing tools)
pip3 install -e .
pip3 install -r requirements-dev.txt
```

### Option 2: Direct installation

```bash
pip3 install hetzner-vrrp-failover
```

### Configuration Setup

1. Create configuration directory:
```bash
sudo mkdir -p /etc/hetzner
```

2. Create configuration file:
```bash
sudo cp config.yaml.example /etc/hetzner-vrrp/config.yaml
sudo chmod 600 /etc/hetzner-vrrp/config.yaml
```

3. Edit the configuration file with your settings:
```bash
sudo vi /etc/hetzner-vrrp/config.yaml
```

## Configuration

Edit `/etc/hetzner-vrrp/config.yaml`:

```yaml
# Hetzner Cloud API Token
hetzner_api_token: "YOUR_API_TOKEN_HERE"

# Floating IPs Configuration
# Only floating IPs matching ALL these labels will be managed
floating_ip_labels:
  role: vrrp
  cluster: production

# Alias IP Configuration
alias_ips:
  - "10.0.0.100/32"
  - "10.0.0.101/32"

# Optional settings
log_file: "/var/log/hetzner-vrrp-failover.log"
log_level: "INFO"
```

### Hetzner Cloud Setup

1. **Create API Token**:
   - Go to Hetzner Cloud Console → Your Project → Security → API Tokens
   - Create a new token with Read & Write permissions

2. **Label your Floating IPs**:
   - Go to Floating IPs in Hetzner Cloud Console
   - Add labels to the IPs you want to manage (e.g., `role=vrrp`, `cluster=production`)

## VyOS Integration

### Method 1: VRRP Transition Scripts

Configure VyOS VRRP to call the script on master transition:

```bash
configure
set high-availability vrrp group VRRP01 transition-script master '/usr/local/bin/hetzner-vrrp-failover -c /etc/hetzner-vrrp/config.yaml'
commit
save
```

### Method 2: Manual Execution

For testing or manual failover:

```bash
# Execute failover
/usr/local/bin/hetzner-vrrp-failover -c /etc/hetzner-vrrp/config.yaml

# Dry run (validate config without making changes)
/usr/local/bin/hetzner-vrrp-failover -c /etc/hetzner-vrrp/config.yaml --dry-run
```

## Usage

```bash
# Execute actual failover
hetzner-vrrp-failover

# Use custom config
hetzner-vrrp-failover -c /path/to/config.yaml

# Dry run mode - validate and show what would be done (NO CHANGES MADE)
hetzner-vrrp-failover --dry-run

# Test locally without Hetzner Cloud server (uses fake server ID)
hetzner-vrrp-failover --dry-run --fake-server-id 12345

# Show help
hetzner-vrrp-failover --help

# Show version
hetzner-vrrp-failover --version
```

### Dry Run Mode

The `--dry-run` flag provides two levels of validation:

**Validation Mode** (with `--dry-run`):
- ✓ Validates configuration file
- ✓ Connects to Hetzner Cloud API (read-only)
- ✓ Shows current state of floating IPs
- ✓ Identifies which IPs need assignment
- ✓ Shows configured alias IPs
- ✗ **Does NOT assign floating IPs**
- ✗ **Does NOT update alias IPs**

**Fake Server ID** (for testing without Hetzner Cloud server):
```bash
# Test locally with a fake server ID
hetzner-vrrp-failover --dry-run --fake-server-id 12345

# Preview what would happen on specific server
hetzner-vrrp-failover --dry-run --fake-server-id 54321 -c config.yaml
```

Benefits:
- ✓ Test configuration without Hetzner Cloud server
- ✓ Develop and debug locally on your laptop
- ✓ Preview changes for specific server ID
- ✓ Safe testing environment

**Important**: `--fake-server-id` only works with `--dry-run` for safety.

**Execution Mode** (without `--dry-run`):
- ✓ Validates configuration
- ✓ Connects to Hetzner Cloud API
- ✓ Assigns floating IPs to this server
- ✓ Updates alias IPs on this server

Example dry-run output:
```
============================================================
DRY RUN - Configuration Validation
============================================================
Server ID: 12345
Log level: INFO

Found 3 floating IP(s) matching labels:
  - 203.0.113.10 (ID: 1001) - unassigned → needs assignment
  - 203.0.113.20 (ID: 1002) - assigned to server 99999 → needs reassignment
  - 203.0.113.30 (ID: 1003) - assigned to server 12345 ✓ (this server)

Configured alias IPs: 2
  - 10.0.0.100/32
  - 10.0.0.101/32

============================================================
Summary:
============================================================
⚠ 2 floating IP(s) need to be assigned
Run without --dry-run to execute failover
```

## How It Works

1. Script reads configuration from YAML file
2. Retrieves current server ID from Hetzner metadata service
3. Queries Hetzner API for floating IPs matching configured labels
4. Assigns all matching floating IPs to the current server
5. Configures alias IPs on the server
6. Logs all actions for monitoring

## Logging

Logs are written to the configured log file (default: `/var/log/hetzner-vrrp-failover.log`) and stdout.

Log levels: DEBUG, INFO, WARNING, ERROR

## Troubleshooting

### Check logs
```bash
tail -f /var/log/hetzner-vrrp-failover.log
```

### Test configuration
```bash
hetzner-vrrp-failover --dry-run
```

### Verify server metadata
```bash
curl http://169.254.169.254/hetzner/v1/metadata/instance-id
```

### Check VRRP status
```bash
show vrrp
```

## Security Considerations

- Store API token securely with restricted permissions (600)
- Use a dedicated API token with minimal required permissions
- Rotate API tokens regularly
- Monitor failover logs for unauthorized access

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/hetzner-vrrp-failover.git
cd hetzner-vrrp-failover

# Install with development dependencies
make install-dev
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make coverage

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Run all linters
make lint

# Format code
make format

# Run individual tools
black hetzner_vrrp_failover tests
flake8 hetzner_vrrp_failover tests
mypy hetzner_vrrp_failover
```

### Project Structure

```
hetzner-vrrp-failover/
├── hetzner_vrrp_failover/    # Main package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration management
│   ├── exceptions.py         # Custom exceptions
│   ├── failover.py           # Main failover logic
│   ├── logger.py             # Logging setup
│   └── metadata.py           # Metadata service client
├── tests/                    # Test suite
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_failover.py
│   └── test_metadata.py
├── config.yaml.example       # Example configuration
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── setup.py                  # Package setup
├── pytest.ini                # Pytest configuration
├── pyproject.toml           # Tool configuration
├── Makefile                 # Development tasks
└── README.md                # This file
```

## License

MIT License - feel free to modify and use as needed.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`make test`)
5. Run code quality checks (`make lint`)
6. Submit a pull request

Please test thoroughly in a staging environment before deploying to production.
