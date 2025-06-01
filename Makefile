# Azure Components Foundry - Unified Build and Deployment
.PHONY: help build push deploy test clean install dev

# Get configuration from manifest
ACR := $(shell yq '.acr' deploy/manifest.yaml 2>/dev/null || echo "myacr.azurecr.io")
IMG := $(shell yq '.imageName' deploy/manifest.yaml 2>/dev/null || echo "azure-components-foundry")
TAG := $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
FULL := $(ACR)/$(IMG):$(TAG)

# Default target
help: ## Show this help message
	@echo "Azure Components Foundry - Build and Deployment"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies using Poetry
	poetry install

dev: ## Set up development environment
	poetry install --with dev
	poetry run pre-commit install || true

build: ## Build the container image
	@echo "Building container image: $(FULL)"
	docker build -t $(FULL) .
	docker tag $(FULL) $(ACR)/$(IMG):latest

push: build ## Build and push the container image
	@echo "Pushing container image: $(FULL)"
	docker push $(FULL)
	docker push $(ACR)/$(IMG):latest

test: ## Run tests
	@echo "Running component tests..."
	poetry run python -m pytest components/ -v
	@echo "Running runtime tests..."
	poetry run python -m pytest runtime/ -v || true

test-local: build ## Test the container locally
	@echo "Testing container locally..."
	docker run --rm -p 8000:8000 -e HANDLER="components.word_count.src.component:predict" $(FULL) &
	sleep 5
	curl -f http://localhost:8000/health || (echo "Health check failed" && exit 1)
	curl -f -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"text":"hello world"}' || (echo "Predict test failed" && exit 1)
	@echo "Local tests passed!"
	docker stop $$(docker ps -q --filter ancestor=$(FULL)) || true

deploy: push ## Deploy all components to all environments
	@echo "Deploying with image: $(FULL)"
	python deploy/run.py --image $(FULL) --manifest deploy/manifest.yaml

deploy-group: push ## Deploy to specific group (usage: make deploy-group GROUP=dev-eastus)
	@echo "Deploying group $(GROUP) with image: $(FULL)"
	python deploy/run.py --image $(FULL) --manifest deploy/manifest.yaml --group $(GROUP)

deploy-service: push ## Deploy to specific service type (usage: make deploy-service SERVICE=containerapp)
	@echo "Deploying service $(SERVICE) with image: $(FULL)"
	python deploy/run.py --image $(FULL) --manifest deploy/manifest.yaml --service $(SERVICE)

dry-run: ## Show what would be deployed without deploying
	@echo "Dry run deployment with image: $(FULL)"
	python deploy/run.py --image $(FULL) --manifest deploy/manifest.yaml --dry-run

validate-manifest: ## Validate the deployment manifest
	@echo "Validating deployment manifest..."
	python -c "import yaml; yaml.safe_load(open('deploy/manifest.yaml'))" && echo "✓ Manifest is valid YAML"
	python deploy/run.py --image $(FULL) --manifest deploy/manifest.yaml --dry-run > /dev/null && echo "✓ Manifest deployment validation passed"

discover: ## Discover components and update manifest
	@echo "Discovering components..."
	poetry run python admin/discover_components.py all --save

manage-manifest: ## Interactive manifest management
	poetry run python admin/manage_manifest.py

clean: ## Clean up build artifacts
	@echo "Cleaning up..."
	docker rmi $(FULL) $(ACR)/$(IMG):latest 2>/dev/null || true
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

login-acr: ## Login to Azure Container Registry
	az acr login --name $(shell echo $(ACR) | cut -d'.' -f1)

# Component-specific targets
component-test: ## Test specific component (usage: make component-test COMPONENT=word_count)
	@echo "Testing component: $(COMPONENT)"
	poetry run python -m pytest components/*/$(COMPONENT)/ -v

component-build: ## Build specific component container (usage: make component-build COMPONENT=word_count)
	@echo "Building component $(COMPONENT) with handler: components.$(COMPONENT).src.component:predict"
	docker build -t $(ACR)/$(IMG):$(COMPONENT)-$(TAG) --build-arg HANDLER="components.$(COMPONENT).src.component:predict" .

# Development targets
dev-run: build ## Run the container locally for development
	docker run --rm -it -p 8000:8000 \
		-e HANDLER="components.word_count.src.component:predict" \
		-v $(PWD)/components:/app/components \
		-v $(PWD)/runtime:/app/runtime \
		$(FULL)

dev-shell: build ## Get a shell in the development container
	docker run --rm -it \
		-v $(PWD):/app \
		--entrypoint /bin/bash \
		$(FULL)

# CI/CD targets
ci-build: ## Build for CI/CD (with proper tagging)
	@echo "CI Build - Image: $(FULL)"
	docker build -t $(FULL) .
	docker tag $(FULL) $(ACR)/$(IMG):$(TAG)

ci-deploy: ci-build ## Full CI/CD deployment pipeline
	docker push $(FULL)
	python deploy/run.py --image $(FULL) --manifest deploy/manifest.yaml

# Information targets
info: ## Show build information
	@echo "Configuration:"
	@echo "  ACR:       $(ACR)"
	@echo "  Image:     $(IMG)"
	@echo "  Tag:       $(TAG)"
	@echo "  Full URI:  $(FULL)"
	@echo "  Git SHA:   $(shell git rev-parse HEAD 2>/dev/null || echo 'unknown')"
	@echo "  Git Branch:$(shell git branch --show-current 2>/dev/null || echo 'unknown')"

status: ## Show deployment status
	@echo "Checking deployment status..."
	@echo "Available groups in manifest:"
	@yq '.groups | keys | .[]' deploy/manifest.yaml
	@echo ""
	@echo "Azure login status:"
	@az account show --query "name" -o tsv 2>/dev/null || echo "Not logged in to Azure"

# Prerequisites check
check-deps: ## Check if required dependencies are installed
	@echo "Checking dependencies..."
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker is required" && exit 1)
	@command -v poetry >/dev/null 2>&1 || (echo "❌ Poetry is required" && exit 1)
	@command -v az >/dev/null 2>&1 || (echo "❌ Azure CLI is required" && exit 1)
	@command -v yq >/dev/null 2>&1 || (echo "❌ yq is required for YAML parsing" && exit 1)
	@command -v git >/dev/null 2>&1 || (echo "❌ Git is required" && exit 1)
	@echo "✅ All dependencies are available"
