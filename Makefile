.PHONY: test-deps test lint run clean

# Install all packages needed for executing tests
# Execute `make test-deps` before executing the test suite
test-deps:
	pip install -r requirements.txt
	playwright install

# Run test suite
test:
	pytest

# Run linting (pre-commit)
lint:
	pre-commit run --all-files

# Run enrichment trace (main entry point)
run:
	python enrich/main.py

# Remove generated cache/output files
clean:
	rm -rf .cache __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
