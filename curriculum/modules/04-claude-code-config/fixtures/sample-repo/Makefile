.PHONY: test lint format clean install help

help:
	@echo "Available targets:"
	@echo "  install   - Install dependencies"
	@echo "  test      - Run tests with coverage"
	@echo "  lint      - Run code linting"
	@echo "  format    - Format code with black"
	@echo "  clean     - Remove build artifacts"

install:
	pip install -r requirements.txt

test:
	pytest tests/ src/ --cov=src --cov-report=term-missing

lint:
	flake8 src/ tests/

format:
	black src/ tests/ config/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
