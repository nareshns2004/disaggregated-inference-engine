# kvwire — see CLAUDE.md "Commands". Keep this file true: a target that does not work yet says so.
PY        ?= python3
BUILD_DIR ?= build
RUN_ID    ?= $(shell date -u +%Y%m%dT%H%M%SZ)

.PHONY: help setup lint typecheck test test-rxe test-gpu test-multinode transport \
        env-manifest topo ceiling bench report clean

help:            ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

setup:           ## dev env (lightweight: pytest/ruff/mypy only)
	$(PY) -m pip install -e ".[dev]"
	pre-commit install || true

lint:            ## ruff
	ruff check . && ruff format --check .

typecheck:       ## mypy --strict on kvwire/ and faultlab/
	mypy

test:            ## CPU tests (GPU/multinode/rxe auto-skipped)
	$(PY) -m pytest

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
