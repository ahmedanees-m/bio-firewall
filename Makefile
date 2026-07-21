# BioFirewall reproducibility entry points. See REPRODUCTION.md for the full clean-image protocol.
.PHONY: install lint test reproduce reproduce-local prereg-sha clean docker-build docker-reproduce

PY ?= python
IMAGE ?= biofirewall

install:                       ## editable install + dev deps (pulls pen-stack>=0.1.0,<0.2.0)
	$(PY) -m pip install -e ".[dev]"

lint:                          ## ruff (the CI lint gate)
	ruff check bio_firewall tests

test:                          ## the full unit suite (validates every committed metric/logic path)
	pytest -q

# `make reproduce` regenerates every headline number that is reproducible FROM THE COMMITTED REPO ALONE
# (open data only): the monotone-combiner monotonicity proof + the full test suite (which validates the cargo/
# conformal/decomp/edit-mech/locus-pos/struct MATH). The data-dependent benchmarks (B1/B2/B6/B8/B9/B10) need the
# local-only data (COSMIC, VISDB, the frozen ESM vectors) and AlphaFold-DB/Foldseek; run them with `reproduce-local`.
reproduce: lint test           ## regenerate the committed-data-reproducible headline numbers
	@echo "=============================================================="
	@echo "BioFirewall: reproduce (committed-data-only headline numbers)"
	@echo "=============================================================="
	$(PY) -c "from bio_firewall.hazard.combine_mono import verify_monotone; import json; r=verify_monotone(); \
print('B7 monotone combiner:', 'PASS' if r['provably_monotone'] and r['hard_rule_exact_refuse'] else 'FAIL', \
'(reps=%d)' % r['reps'])"
	@echo ""
	@echo "Frozen, pre-registered results for the data-dependent benchmarks are in prereg/ws_biofirewall.yaml"
	@echo "(blocks results_2026_06_17 / tier1_results / tier2_results / tier3_results). Regenerate them with:"
	@echo "    make reproduce-local"
	@echo "All committed math is validated by the test suite above (make test)."

# Full regeneration including the restricted/large local-only data. Set the env vars to your local paths first.
#   PEN_STACK_HOME   = pen-stack checkout (Guardian configs)
#   BF_BENCH_ORACLES = dir with cosmic_cgc_v104.tsv (+ oncokb), local-only, NEVER committed
#   BF_B2_DIR        = the frozen Benchmark-2 dir (vectors.npz + the public-proxy fastas)
#   BF_VISDB_DIR     = VISDB per-virus CSVs ; BF_GENE_COORDS = GENCODE gene_coords.parquet
reproduce-local:               ## full regeneration (needs the local-only data + mmseqs/foldseek/torch)
	$(PY) -m bio_firewall.eval.hazard_bench.run_all                                  # B1 / B3 / B4
	$(PY) -c "from bio_firewall.eval.hazard_bench import conformal_bench as c; import json; print(json.dumps(c.run()['gate']))"   # B4b
	$(PY) -c "from bio_firewall.eval.hazard_bench import edit_mech_bench as b; import json; print(json.dumps(b.run()))"           # B8
	$(PY) -c "from bio_firewall.eval.hazard_bench import locus_outcome as l; import json; print(json.dumps(l.run_visdb()['overall']))"  # B6
	$(PY) -c "from bio_firewall.eval.hazard_bench import locus_pos_bench as b; import json; print(json.dumps(b.run_visdb()))"     # B9
	@echo "B2 (cargo gate) / B2b (decorr) / B10 (struct) need mmseqs/torch/Foldseek + AF-DB; see docs/BENCHMARK.md."

prereg-sha:                    ## print the SHA-256 of the SHA-locked pre-registration
	$(PY) -c "import hashlib; print('prereg/ws_biofirewall.yaml sha256 =', hashlib.sha256(open('prereg/ws_biofirewall.yaml','rb').read()).hexdigest())"

docker-build:                  ## build the reproducible container image (pins Python 3.11)
	docker build -t $(IMAGE) .

docker-reproduce: docker-build ## build the image, then run the committed-data reproduction inside it
	docker run --rm $(IMAGE) make reproduce

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache bf_* 2>/dev/null || true
