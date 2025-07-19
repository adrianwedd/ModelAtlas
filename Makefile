.PHONY: test-deps

# Install all packages needed for executing tests
# Execute `make test-deps` before executing the test suite

test-deps:
	pip install -r requirements.txt
	playwright install
