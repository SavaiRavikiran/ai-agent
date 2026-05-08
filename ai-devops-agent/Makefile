.PHONY: install test test-security build push deploy-staging deploy-prod logs shell rag-ingest smoke-test port-forward

install:
	poetry install

test:
	poetry run pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

test-security:
	poetry run bandit -r agent tools rag api config -ll
	poetry run safety check || true

build:
	docker build -t ai-devops-agent:latest .

push:
	docker tag ai-devops-agent:latest $(REGISTRY)/ai-devops-agent:latest
	docker push $(REGISTRY)/ai-devops-agent:latest

deploy-staging:
	helm upgrade --install ai-devops-agent ./k8s/helm -n ai-agent -f k8s/helm/values.yaml

deploy-prod:
	helm upgrade --install ai-devops-agent ./k8s/helm -n production -f k8s/helm/values.yaml

logs:
	kubectl logs -f deployment/ai-devops-agent -n ai-agent

shell:
	kubectl exec -it deployment/ai-devops-agent -n ai-agent -- sh

rag-ingest:
	PYTHONPATH=. python -m rag.ingest_cli ingest-dir --path rag/sample_documents --type runbook --tags all
	PYTHONPATH=. python -m rag.ingest_cli stats

smoke-test:
	./scripts/smoke_test.sh

port-forward:
	kubectl port-forward deployment/ai-devops-agent 8080:8080 -n ai-agent
