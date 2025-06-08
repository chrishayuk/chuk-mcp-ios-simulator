.PHONY: clean clean-pyc clean-build clean-test clean-all test test-cov run-mcp run-cli build publish publish-test publish-check help install dev-install lint format typecheck check info demo setup-dev

# Default target
help:
	@echo "🍎 iOS Device Control MCP Server - Available targets:"
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  install       - Install package in current environment"
	@echo "  dev-install   - Install package in development mode with dev dependencies"
	@echo "  setup-dev     - Full development setup (install + check iOS tools)"
	@echo ""
	@echo "🧹 Cleaning:"
	@echo "  clean         - Remove Python bytecode and basic artifacts"
	@echo "  clean-all     - Deep clean everything (pyc, build, test, cache)"
	@echo "  clean-pyc     - Remove Python bytecode files"
	@echo "  clean-build   - Remove build artifacts"
	@echo "  clean-test    - Remove test artifacts"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test          - Run tests with pytest"
	@echo "  test-cov      - Run tests with coverage reporting"
	@echo "  lint          - Run code linting (ruff)"
	@echo "  format        - Format code with ruff"
	@echo "  typecheck     - Run type checking with mypy"
	@echo "  check         - Run all code quality checks"
	@echo ""
	@echo "🚀 Running:"
	@echo "  run-main      - Run the main dispatcher (shows help)"
	@echo "  run-mcp       - Run the MCP server"
	@echo "  run-cli       - Run the CLI interface"
	@echo "  run-cli-status - Run CLI status command"
	@echo "  demo          - Run interactive demo"
	@echo "  demo-auto     - Run automated demo"
	@echo "  demo-mcp      - Run MCP end-to-end demo"
	@echo "  test-sim      - Test simulator connectivity"
	@echo ""
	@echo "📦 Building & Publishing:"
	@echo "  build         - Build the project"
	@echo "  publish-check - Check package before publishing"
	@echo "  publish-test  - Publish to test PyPI"
	@echo "  publish       - Build and publish to PyPI"
	@echo ""
	@echo "ℹ️  Information:"
	@echo "  info          - Show project and environment info"
	@echo "  check-ios     - Check iOS development environment"

# Basic clean - Python bytecode and common artifacts
clean: clean-pyc clean-build
	@echo "🧹 Basic clean complete."

# Remove Python bytecode files and __pycache__ directories
clean-pyc:
	@echo "🧹 Cleaning Python bytecode files..."
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@find . -type f -name '*.pyo' -delete 2>/dev/null || true
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true

# Remove build artifacts
clean-build:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info 2>/dev/null || true
	@rm -rf .eggs/ 2>/dev/null || true
	@find . -name '*.egg' -exec rm -f {} + 2>/dev/null || true

# Remove test artifacts
clean-test:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .tox/ 2>/dev/null || true
	@rm -rf .cache/ 2>/dev/null || true
	@find . -name '.coverage.*' -delete 2>/dev/null || true

# Deep clean - everything including demo outputs
clean-all: clean-pyc clean-build clean-test
	@echo "🧹 Deep cleaning..."
	@rm -rf .mypy_cache/ 2>/dev/null || true
	@rm -rf .ruff_cache/ 2>/dev/null || true
	@rm -rf .uv/ 2>/dev/null || true
	@rm -rf node_modules/ 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@find . -name 'Thumbs.db' -delete 2>/dev/null || true
	@find . -name '*.log' -delete 2>/dev/null || true
	@find . -name '*.tmp' -delete 2>/dev/null || true
	@find . -name '*~' -delete 2>/dev/null || true
	@echo "🧹 Cleaning demo outputs..."
	@rm -rf simulator_demo_output/ 2>/dev/null || true
	@rm -rf mcp_e2e_demo_output/ 2>/dev/null || true
	@rm -rf techmeme_news/ 2>/dev/null || true
	@rm -rf ~/.ios-device-control/sessions/*.json 2>/dev/null || true
	@echo "✅ Deep clean complete."

# Install package
install:
	@echo "📦 Installing package..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install .; \
	else \
		pip install .; \
	fi

# Install package in development mode with dev dependencies
dev-install:
	@echo "📦 Installing package in development mode..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -e ".[dev]"; \
	else \
		pip install -e ".[dev]"; \
	fi

# Full development setup
setup-dev: dev-install check-ios
	@echo "🎯 Development setup complete!"
	@echo "💡 Try: make demo"

# Run tests
test:
	@echo "🧪 Running tests..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ -v; \
	elif command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v; \
	else \
		python -m pytest tests/ -v; \
	fi

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ --cov=src/chuk_mcp_ios --cov-report=html --cov-report=term --cov-report=xml -v; \
	else \
		pytest tests/ --cov=src/chuk_mcp_ios --cov-report=html --cov-report=term --cov-report=xml -v; \
	fi

# Run the main dispatcher (new unified entry point)
run-main:
	@echo "🚀 Starting chuk-mcp-ios main dispatcher..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=src uv run python -m chuk_mcp_ios.main; \
	else \
		PYTHONPATH=src python3 -m chuk_mcp_ios.main; \
	fi

# Run the MCP server (via dispatcher)
run-mcp:
	@echo "🚀 Starting MCP iOS Server..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=src uv run python -m chuk_mcp_ios.main mcp; \
	else \
		PYTHONPATH=src python3 -m chuk_mcp_ios.main mcp; \
	fi

# Run the CLI interface (via dispatcher)
run-cli:
	@echo "🚀 Starting iOS Control CLI..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=src uv run python -m chuk_mcp_ios.main cli; \
	else \
		PYTHONPATH=src python3 -m chuk_mcp_ios.main cli; \
	fi

# Run CLI with status command
run-cli-status:
	@echo "🚀 Running iOS Control CLI Status..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=src uv run python -m chuk_mcp_ios.main cli status; \
	else \
		PYTHONPATH=src python3 -m chuk_mcp_ios.main cli status; \
	fi

# Run interactive demo
demo:
	@echo "🎮 Starting Interactive iOS Demo..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python examples/interactive_demo.py; \
	else \
		python3 examples/interactive_demo.py; \
	fi

# Run automated demo
demo-auto:
	@echo "🤖 Starting Automated iOS Demo..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python examples/automated_demo.py; \
	else \
		python3 examples/automated_demo.py; \
	fi

# Run MCP E2E demo
demo-mcp:
	@echo "🔧 Starting MCP End-to-End Demo..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python examples/e2e_mcp_demo.py; \
	else \
		python3 examples/e2e_mcp_demo.py; \
	fi

# Test simulator connectivity
test-sim:
	@echo "📱 Testing iOS Simulator connectivity..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python examples/test_simulator.py; \
	else \
		python3 examples/test_simulator.py; \
	fi

# Run Techmeme news capture demo
demo-news:
	@echo "📰 Starting Techmeme News Demo..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python examples/techmeme.py; \
	else \
		python3 examples/techmeme.py; \
	fi

# Build the project using the pyproject.toml configuration
build: clean-build
	@echo "🔨 Building project..."
	@if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		python3 -m build; \
	fi
	@echo "✅ Build complete. Distributions are in the 'dist' folder."

# Check package before publishing (using external script)
publish-check: build
	@echo "🔍 Checking package before publishing..."
	@if [ -f "scripts/validate_package.py" ]; then \
		python3 scripts/validate_package.py; \
	else \
		echo "📋 Basic package validation..."; \
		echo "📦 Built distributions:"; \
		ls -la dist/ 2>/dev/null || echo "❌ No dist directory found"; \
		if command -v twine >/dev/null 2>&1; then \
			echo "📋 Running twine check..."; \
			twine check dist/* 2>/dev/null || echo "⚠️  Twine check had warnings"; \
		else \
			echo "📋 Twine not available, basic validation only"; \
		fi; \
		echo "✅ Basic validation complete"; \
		echo "💡 For detailed validation, create scripts/validate_package.py"; \
	fi

# Check for .pypirc file
check-pypirc:
	@echo "🔐 Checking for .pypirc configuration..."
	@if [ -f "$$HOME/.pypirc" ]; then \
		echo "✅ Found .pypirc file at $$HOME/.pypirc"; \
		echo "📋 Configuration sections:"; \
		grep -E '^\[.*\]$$' $$HOME/.pypirc || echo "No sections found"; \
	else \
		echo "❌ No .pypirc file found at $$HOME/.pypirc"; \
		echo "💡 Create .pypirc with:"; \
		echo "   [pypi]"; \
		echo "   username = __token__"; \
		echo "   password = pypi-your-token-here"; \
	fi

# Publish the package to PyPI using .pypirc
publish: build check-pypirc
	@echo "📤 Publishing package to PyPI using .pypirc..."
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist 2>/dev/null)" ]; then \
		echo "❌ Error: No distribution files found. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "🔍 Found distribution files:"
	@ls -la dist/
	@echo ""
	@if [ ! -f "$$HOME/.pypirc" ]; then \
		echo "❌ Error: .pypirc file not found at $$HOME/.pypirc"; \
		echo "💡 Create .pypirc file with your PyPI token:"; \
		echo "   [pypi]"; \
		echo "   username = __token__"; \
		echo "   password = pypi-your-token-here"; \
		exit 1; \
	fi
	@if command -v twine >/dev/null 2>&1; then \
		echo "📤 Using twine to publish (reads .pypirc automatically)..."; \
		last_build=$$(ls -t dist/*.tar.gz dist/*.whl 2>/dev/null | head -n 2); \
		if [ -z "$$last_build" ]; then \
			echo "❌ Error: No valid distribution files found."; \
			exit 1; \
		fi; \
		echo "📤 Uploading: $$last_build"; \
		twine upload $$last_build; \
	elif command -v uv >/dev/null 2>&1; then \
		echo "📤 Using uv to publish..."; \
		echo "⚠️  Note: uv publish may not read .pypirc reliably"; \
		echo "💡 If prompted for credentials, use __token__ and your PyPI token"; \
		uv publish dist/* || { \
			echo "❌ uv publish failed. Trying with explicit credentials..."; \
			if [ -f "$$HOME/.pypirc" ]; then \
				USERNAME=$$(grep -A 5 '^\[pypi\]' $$HOME/.pypirc | grep '^username' | cut -d'=' -f2 | tr -d ' '); \
				PASSWORD=$$(grep -A 5 '^\[pypi\]' $$HOME/.pypirc | grep '^password' | cut -d'=' -f2 | tr -d ' '); \
				if [ -n "$$USERNAME" ] && [ -n "$$PASSWORD" ]; then \
					echo "📤 Using credentials from .pypirc..."; \
					uv publish dist/* --username "$$USERNAME" --password "$$PASSWORD"; \
				else \
					echo "❌ Could not extract credentials from .pypirc"; \
					exit 1; \
				fi; \
			else \
				exit 1; \
			fi; \
		}; \
	else \
		echo "❌ Neither twine nor uv found for publishing"; \
		echo "   Install with: pip install twine"; \
		exit 1; \
	fi
	@echo "✅ Package published successfully!"
	@echo "🎉 Users can now run:"
	@echo "   uvx chuk-mcp-ios cli status"
	@echo "   uvx chuk-mcp-ios mcp"

# Publish to test PyPI using .pypirc
publish-test: build check-pypirc
	@echo "📤 Publishing to test PyPI using .pypirc..."
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist 2>/dev/null)" ]; then \
		echo "❌ Error: No distribution files found. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "🔍 Found distribution files:"
	@ls -la dist/
	@echo ""
	@if command -v twine >/dev/null 2>&1; then \
		echo "📤 Using twine to publish to test PyPI..."; \
		last_build=$$(ls -t dist/*.tar.gz dist/*.whl 2>/dev/null | head -n 2); \
		if [ -z "$$last_build" ]; then \
			echo "❌ Error: No valid distribution files found."; \
			exit 1; \
		fi; \
		echo "📤 Uploading to test PyPI: $$last_build"; \
		if grep -q '^\[testpypi\]' $$HOME/.pypirc 2>/dev/null; then \
			echo "📋 Using testpypi section from .pypirc"; \
			twine upload --repository testpypi $$last_build; \
		else \
			echo "⚠️  No [testpypi] section in .pypirc, using default test PyPI"; \
			twine upload --repository-url https://test.pypi.org/legacy/ $$last_build; \
		fi; \
	elif command -v uv >/dev/null 2>&1; then \
		echo "📤 Using uv to publish to test PyPI..."; \
		uv publish --repository testpypi dist/*; \
	else \
		echo "❌ Neither uv nor twine found for publishing"; \
		echo "   Install with: pip install twine"; \
		exit 1; \
	fi
	@echo "✅ Package published to test PyPI!"
	@echo "🧪 Test with:"
	@echo "   uvx --index-url https://test.pypi.org/simple/ chuk-mcp-ios cli status"

# Check code quality
lint:
	@echo "🔍 Running linters..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff check src/ examples/ tests/; \
		uv run ruff format --check src/ examples/ tests/; \
	elif command -v ruff >/dev/null 2>&1; then \
		ruff check src/ examples/ tests/; \
		ruff format --check src/ examples/ tests/; \
	else \
		echo "⚠️  Ruff not found. Install with: pip install ruff"; \
	fi

# Fix code formatting
format:
	@echo "🎨 Formatting code..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff format src/ examples/ tests/; \
		uv run ruff check --fix src/ examples/ tests/; \
	elif command -v ruff >/dev/null 2>&1; then \
		ruff format src/ examples/ tests/; \
		ruff check --fix src/ examples/ tests/; \
	else \
		echo "⚠️  Ruff not found. Install with: pip install ruff"; \
	fi

# Type checking
typecheck:
	@echo "🔍 Running type checker..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run mypy src/chuk_mcp_ios/; \
	elif command -v mypy >/dev/null 2>&1; then \
		mypy src/chuk_mcp_ios/; \
	else \
		echo "⚠️  MyPy not found. Install with: pip install mypy"; \
	fi

# Run all checks
check: lint typecheck test
	@echo "✅ All checks completed."

# Check iOS development environment
check-ios:
	@echo "📱 Checking iOS development environment..."
	@echo "Checking Xcode Command Line Tools..."
	@if command -v xcrun >/dev/null 2>&1; then \
		echo "✅ Xcode Command Line Tools found"; \
		if xcrun simctl help >/dev/null 2>&1; then \
			echo "✅ iOS Simulator tools available"; \
			echo "📊 Available simulators:"; \
			xcrun simctl list devices | grep -E "(iPhone|iPad)" | head -5; \
		else \
			echo "❌ iOS Simulator tools not available"; \
		fi; \
	else \
		echo "❌ Xcode Command Line Tools not found"; \
		echo "💡 Install with: xcode-select --install"; \
	fi
	@echo ""
	@echo "Checking optional tools..."
	@if command -v idb >/dev/null 2>&1; then \
		echo "✅ idb found (real device support available)"; \
	else \
		echo "⚠️  idb not found (optional - for real device support)"; \
		echo "💡 Install with: brew install idb-companion"; \
	fi

# Show project info
info:
	@echo "🍎 iOS Device Control MCP Server"
	@echo "================================="
	@if [ -f "pyproject.toml" ]; then \
		echo "📄 pyproject.toml found"; \
		if command -v uv >/dev/null 2>&1; then \
			echo "🔧 UV version: $$(uv --version)"; \
		fi; \
		if command -v python >/dev/null 2>&1; then \
			echo "🐍 Python version: $$(python --version)"; \
		fi; \
	else \
		echo "❌ No pyproject.toml found"; \
	fi
	@echo "📁 Current directory: $$(pwd)"
	@echo "📂 Source structure:"
	@echo "   src/chuk_mcp_ios/    - Main package"
	@echo "   examples/            - Demo scripts"
	@echo "   tests/               - Test suite"
	@echo ""
	@echo "🎯 Quick start:"
	@echo "   make setup-dev       - Set up development environment"
	@echo "   make test-sim        - Test simulator connectivity"
	@echo "   make run-cli-status  - Check system status"
	@echo "   make demo            - Run interactive demo"
	@echo "   make run-cli         - Start CLI interface"
	@echo "   make run-mcp         - Start MCP server"
	@echo ""
	@echo "📤 Publishing workflow:"
	@echo "   make publish-check   - Validate package"
	@echo "   make publish-test    - Test on test PyPI"
	@echo "   make publish         - Publish to PyPI"
	@echo "   # Then users can: uvx chuk-mcp-ios cli status"
	@echo ""
	@echo "📊 Git status:"
	@git status --porcelain 2>/dev/null || echo "Not a git repository"

# Development shortcuts
dev: setup-dev
	@echo "🎯 Development environment ready!"

quick-test: test-sim demo-auto
	@echo "🚀 Quick test complete!"

all-demos: demo-auto demo-mcp demo-news
	@echo "🎬 All demos complete!"