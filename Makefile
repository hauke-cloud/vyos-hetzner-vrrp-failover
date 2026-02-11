.PHONY: help install install-dev test coverage lint format clean

help:
	@echo "Available targets:"
	@echo "  install      - Install package and dependencies"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  lint         - Run code quality checks"
	@echo "  format       - Format code with black and isort"
	@echo "  clean        - Remove generated files"

install:
	pip install .

install-dev:
	pip install -e .
	pip install -r requirements-dev.txt

test:
	pytest

coverage:
	pytest --cov=hetzner_vrrp_failover --cov-report=html --cov-report=term

lint:
	flake8 hetzner_vrrp_failover tests
	mypy hetzner_vrrp_failover
	black --check hetzner_vrrp_failover tests
	isort --check-only hetzner_vrrp_failover tests

format:
	black hetzner_vrrp_failover tests
	isort hetzner_vrrp_failover tests

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
