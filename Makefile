.PHONY: help install dev test lint format clean run doctor

help:
	@echo "Drift CLI - Development Commands"
	@echo ""
	@echo "  make install    - Install Drift CLI"
	@echo "  make dev        - Setup development environment"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make run        - Run Drift doctor"
	@echo "  make doctor     - Check system setup"

install:
	@echo "Installing Drift CLI..."
	@./install.sh

dev:
	@echo "Setting up development environment..."
	pip install -e ".[dev]"
	@echo "✓ Development environment ready"

test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=drift_cli --cov-report=html --cov-report=term

lint:
	@echo "Running linter..."
	ruff check drift_cli/

format:
	@echo "Formatting code..."
	ruff format drift_cli/
	@echo "✓ Code formatted"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

run:
	drift doctor

doctor:
	drift doctor
