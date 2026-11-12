# kvwire — see CLAUDE.md "Commands". Keep this file true: a target that does not work yet says so.
PY        ?= python3
BUILD_DIR ?= build
RUN_ID    ?= $(shell date -u +%Y%m%dT%H%M%SZ)

.PHONY: help setup check lint typecheck test test-transport test-rxe test-gpu test-multinode \
        transport check-numbers env-manifest topo ceiling bench report clean

help:            ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

setup:           ## dev env in .venv (laptop tier: pytest/ruff/mypy, no torch/vLLM) + pre-commit
	uv venv --python 3.10 .venv
	uv pip install --python .venv/bin/python -e ".[dev,bench]"
	.venv/bin/pre-commit install

check: lint typecheck test check-numbers  ## everything the Python CI job runs

lint:            ## ruff
	ruff check . && ruff format --check .

typecheck:       ## mypy --strict on kvwire/, faultlab/ and bench/
	mypy

test:            ## CPU tests (GPU/multinode/rxe auto-skipped)
	$(PY) -m pytest

test-transport:  ## C++ unit tests (after `make transport`)
	ctest --test-dir $(BUILD_DIR) --output-on-failure -L unit

check-numbers:   ## fail on perf numbers in docs without provenance
	$(PY) scripts/check_numbers.py README.md docs/*.md docs/adr/*.md

test-rxe:        ## transport logic tests over SoftRoCE (non-performance)
	$(PY) -m pytest --run-rxe -m rxe
	ctest --test-dir $(BUILD_DIR) --output-on-failure

test-gpu:        ## GPU tests
	$(PY) -m pytest --run-gpu -m gpu

test-multinode:  ## two-node tests (reads hosts from docs/ENVIRONMENT.md allowlist)
	$(PY) -m pytest --run-multinode -m multinode

transport:       ## configure + build C++ transport (verbs backend only if libibverbs found)
	cmake -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=RelWithDebInfo
	cmake --build $(BUILD_DIR) -j

env-manifest:    ## write docs/ENVIRONMENT.md generated section (read-only probes)
	$(PY) scripts/env_manifest.py --write docs/ENVIRONMENT.md

topo:            ## GPU<->NIC affinity -> artifacts/topology.json
	$(PY) -m kvwire.topology.discover --out artifacts/topology.json

ceiling:         ## perftest sweep -> bench/results/<run_id>/ceiling/  (needs a peer host)
	scripts/ceiling_sweep.sh bench/results/$(RUN_ID)/ceiling

bench:           ## serving experiment: make bench SCENARIO=bench/scenarios/x.yaml
	@test -n "$(SCENARIO)" || (echo "SCENARIO=<path.yaml> required" && exit 2)
	$(PY) -m bench.loadgen.run --scenario $(SCENARIO) --out bench/results/$(RUN_ID)

report:          ## make report RUN=<run_id>
	@test -n "$(RUN)" || (echo "RUN=<run_id> required" && exit 2)
	$(PY) -m bench.report.generate bench/results/$(RUN)

clean:
	rm -rf $(BUILD_DIR) .pytest_cache .mypy_cache .ruff_cache
