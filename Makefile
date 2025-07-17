.PHONY: test-deps

# Install all packages needed for running tests
# Run `make test-deps` before executing the test suite

test-deps:
	pip install -r requirements.txt
	playwright install
