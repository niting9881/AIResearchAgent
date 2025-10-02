# Makefile for LLM Research Intelligence Hub

.PHONY: help install setup test lint format clean docker-up docker-down run-streamlit run-airflow

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make setup            - Set up the project (create dirs, copy env)"
	@echo "  make test             - Run tests"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo "  make clean            - Clean up generated files"
	@echo "  make docker-up        - Start all services with Docker Compose"
	@echo "  make docker-down      - Stop all Docker services"
	@echo "  make docker-logs      - View Docker logs"
	@echo "  make run-streamlit    - Run Streamlit app locally"
	@echo "  make run-airflow      - Run Airflow locally"
	@echo "  make init-db          - Initialize databases"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Setup project
setup:
	@echo "Setting up project..."
	mkdir -p data/raw data/processed data/evaluation logs airflow/dags airflow/logs airflow/plugins
	@if not exist .env copy .env.example .env
	@echo "Setup complete! Please edit .env with your API keys."

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linters
lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/ --max-line-length=120
	pylint src/ --disable=C0114,C0115,C0116 --max-line-length=120
	mypy src/ --ignore-missing-imports

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Clean up
clean:
	@echo "Cleaning up..."
	if exist __pycache__ rmdir /s /q __pycache__
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .coverage del /q .coverage
	if exist htmlcov rmdir /s /q htmlcov
	if exist dist rmdir /s /q dist
	if exist build rmdir /s /q build
	if exist *.egg-info rmdir /s /q *.egg-info
	@for /r %%i in (*.pyc) do @del /q "%%i"
	@for /r %%i in (*.pyo) do @del /q "%%i"
	@echo "Cleanup complete!"

# Docker commands
docker-up:
	docker-compose up -d
	@echo "Services started! Access points:"
	@echo "  - Streamlit: http://localhost:8501"
	@echo "  - Airflow: http://localhost:8080 (admin/admin)"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Qdrant: http://localhost:6333/dashboard"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

docker-build:
	docker-compose build --no-cache

# Run locally
run-streamlit:
	streamlit run src/app/streamlit_app.py

run-airflow:
	@set AIRFLOW_HOME=%cd%\airflow
	airflow webserver -p 8080 & airflow scheduler

# Database initialization
init-db:
	python scripts/init_db.py

# Run evaluation
evaluate:
	python scripts/run_evaluation.py

# Generate test data
generate-test-data:
	python scripts/generate_test_data.py
