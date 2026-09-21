"""Acceptance: data-grounded locus axis, signed passport, tamper-evident audit, the per-axis
interception benchmark, and red-team robustness."""
from __future__ import annotations

from bio_firewall import screen
from bio_firewall.audit import AuditLog
from bio_firewall.data import gene_roles
from bio_firewall.eval import legitimate_research_not_blocked, reframing_resistance, run
from bio_firewall.passport import verify_passport


# ---- Axis 2 locus on real CC0 data (CancerMine/DepMap) ----
def test_locus_axis_uses_real_cancermine_depmap_data_when_vendored():
    roles = gene_roles("TP53")
    if not roles:                                    # vendored_data absent on a bare checkout -> skip
        return
    assert "TSG" in roles                            # TP53 is a tumour suppressor in CancerMine
    v = screen({"intent": "insert reporter", "gene": "TP53"})
    assert v["decision"] == "flag_for_review"        # TSG disruption flagged (not blocked)
    assert v["axes"]["locus"]["rule_id"] in ("locus.tumor_suppressor_disruption", "locus.genotoxic_proximity")
    assert v["axes"]["locus"]["extrapolating"] is True   # mechanism flag, not a validated cancer rate


# ---- P4 signed passport ----
def test_passport_is_signed_and_tamper_evident():
    v = screen({"intent": "therapeutic insert", "gene": "AAVS1"})
    p = v["passport"]
    assert verify_passport(p) is True
    p2 = dict(p)
    p2["decision"] = "refuse"                         # tamper
    assert verify_passport(p2) is False


# ---- P7 tamper-evident audit ----
def test_audit_log_chains_and_detects_tampering():
    log = AuditLog()
    for plan in ({"gene": "AAVS1"}, {"gene": "LMO2"}, {"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}):
        screen(plan, audit=log)
    assert len(log.entries) == 3 and log.verify() is True
    log.entries[0]["record"]["decision"] = "refuse"  # retroactive edit (the first plan decided 'allow')
    assert log.verify() is False


# ---- Section 7 per-axis interception benchmark ----
def test_benchmark_intercepts_what_homology_misses():
    r = run()
    assert r["homology_baseline_interception"] == 0.0     # homology screen is blind to structural hazards
    assert r["overall_interception"] >= 0.9               # the five-axis firewall catches them
    assert r["false_block_rate"] == 0.0                   # benign somatic plans are not blocked
    for axis in ("locus", "edit_type", "germline", "scale"):
        assert r["by_axis"][axis]["caught"] == r["by_axis"][axis]["n"]   # full interception per differentiating axis


# ---- P6 red-team ----
def test_reframing_does_not_flip_refuse_to_allow():
    assert reframing_resistance()["all_refused"] is True


def test_legitimate_research_is_flagged_not_blocked():
    assert legitimate_research_not_blocked()["none_blocked"] is True


# --- audit chain: what it detects, and what needs an out-of-band anchor ---------------------------
def test_keyed_chain_resists_recomputation():
    """Unkeyed, anyone who can write the store can recompute a self-consistent chain. Under a key,
    recomputation requires the key, which is what makes tampering detectable against an adversary
    rather than only against accident."""
    from bio_firewall.audit.log import AuditLog, _hash
    for key, recompute_should_pass in ((None, True), (b"deployment-secret", False)):
        log = AuditLog(key=key)
        for i in range(4):
            log.append({"event": "screen", "i": i})
        log.entries[1]["record"]["i"] = 99                       # tamper
        prev = log.entries[0]["hash"]                            # then recompute downstream
        for e in log.entries[1:]:
            e["prev"] = prev
            e["hash"] = _hash(prev, e["record"], None)           # attacker has no key
            prev = e["hash"]
        assert log.verify() is recompute_should_pass


def test_tail_truncation_needs_an_out_of_band_anchor():
    """Every prefix of a valid chain is itself valid, so truncation cannot be detected from the log
    alone. It is detected against a retained head digest or entry count."""
    from bio_firewall.audit.log import AuditLog
    log = AuditLog()
    for i in range(5):
        log.append({"event": "screen", "i": i})
    head, n = log.head, len(log.entries)
    del log.entries[3:]                                          # drop the tail
    assert log.verify() is True                                  # undetectable on its own
    assert log.verify(expected_head=head) is False               # detected against the anchor
    assert log.verify(expected_len=n) is False


def test_verify_returns_false_on_a_malformed_entry():
    from bio_firewall.audit.log import AuditLog
    log = AuditLog()
    log.append({"event": "screen"})
    log.entries.append({"prev": log.head})                       # no 'record' key
    assert log.verify() is False


def test_tampered_file_is_flagged_on_load(tmp_path):
    """A log was previously extended without checking what it was being extended onto."""
    import json
    from bio_firewall.audit.log import AuditLog
    p = tmp_path / "audit.jsonl"
    log = AuditLog(p)
    log.append({"event": "screen", "i": 0})
    log.append({"event": "screen", "i": 1})
    lines = p.read_text(encoding="utf-8").splitlines()
    e = json.loads(lines[0])
    e["record"]["i"] = 99
    p.write_text(json.dumps(e) + "\n" + lines[1] + "\n", encoding="utf-8")
    assert AuditLog(p).loaded_intact is False


# --- a development-key passport says so, inside the signature ------------------------------------
def test_dev_key_passport_is_self_identifying(monkeypatch):
    from bio_firewall.passport.sign import sign_passport, verify_passport
    v = {"decision": "allow", "ruleset_version": "1", "evidence": []}
    monkeypatch.delenv("BIOFW_PASSPORT_KEY", raising=False)
    dev = sign_passport({"intent": "x"}, v)
    assert dev.get("dev_key") is True
    assert verify_passport(dev)
    assert verify_passport({k: val for k, val in dev.items() if k != "dev_key"}) is False  # signed
    monkeypatch.setenv("BIOFW_PASSPORT_KEY", "a-real-deployment-key")
    prod = sign_passport({"intent": "x"}, v)
    assert "dev_key" not in prod
    assert verify_passport(prod)


# --- a missing vendored table is recorded, not silently absorbed ---------------------------------
def test_missing_vendored_resource_is_visible(monkeypatch):
    import bio_firewall.data as D
    assert D.missing_vendored() == []                            # a complete install
    monkeypatch.setattr(D, "_VD", D._VD / "does-not-exist")
    assert "locus_genes.parquet" in D.missing_vendored()
    monkeypatch.setenv("BIOFW_REQUIRE_VENDORED_DATA", "1")
    import pytest
    with pytest.raises(RuntimeError, match="vendored hazard data missing"):
        D.require_vendored_data()


def test_unmapped_fields_are_recorded_on_the_verdict():
    """The five-axis contract drops keys it does not map, which is what makes it tool-agnostic and
    is also how content submitted under an unexpected name avoids every rule. The verdict records
    which keys were dropped, so a clear result on a partially read artefact is distinguishable."""
    from bio_firewall import screen
    from bio_firewall.adapters.generic_artifact import unmapped_keys
    plain = {"intent": "insert a Factor IX cassette", "gene": "AAVS1"}
    assert unmapped_keys(plain) == []
    assert "unmapped_keys" not in screen(plain)
    carrying = {**plain, "payload_notes": "ricin A chain", "vector": "AAV9"}
    assert unmapped_keys(carrying) == ["payload_notes", "vector"]
    assert screen(carrying)["unmapped_keys"] == ["payload_notes", "vector"]
