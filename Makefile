CONTAINER_ENGINE ?= docker
IMAGE ?= sabaaccessory-dev

.PHONY: help check nix-check fmt docker-build docker-check docker-shell clean

help:
	@echo "check         Run repository validation in the Nix development shell"
	@echo "nix-check     Evaluate and run all flake checks"
	@echo "fmt           Format Nix and shell files"
	@echo "docker-build  Build the pinned development image"
	@echo "docker-check  Run validation in the container without network access"
	@echo "docker-shell  Open an interactive container shell"
	@echo "clean         Remove generated repository artifacts"

check:
	@bash scripts/check.sh

nix-check:
	@nix flake check

fmt:
	@nix fmt
	@shfmt --indent 2 --case-indent --write scripts .github/scripts

docker-build:
	@$(CONTAINER_ENGINE) build --tag $(IMAGE) .

docker-check: docker-build
	@$(CONTAINER_ENGINE) run --rm --network none -v "$(CURDIR):/workspace" -w /workspace $(IMAGE) make check

docker-shell: docker-build
	@$(CONTAINER_ENGINE) run --rm -it -v "$(CURDIR):/workspace" -w /workspace $(IMAGE) bash

clean:
	@rm -rf build Website/docs Website/index.json .work result result-*
