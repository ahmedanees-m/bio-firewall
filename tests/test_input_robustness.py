"""Input robustness: a governance layer sits in front of other people's agents, so a malformed plan must produce a
screen result, not a stack trace.
"""
from bio_firewall.hazard.germline import screen_germline
from bio_firewall.intercept.spine import screen


def test_germline_bool_is_coerced_not_thrown():
    # the documented schema is a dict; a caller passing a bare boolean must not raise (the call itself is the test)
    assert screen_germline({"intent": "x", "germline": True}) is not None
    assert screen_germline({"intent": "x", "germline": False}) is not None
    # a non-dict locus is tolerated too
    assert screen_germline({"intent": "x", "germline": {"heritable": True}, "locus": True}) is not None


def test_screen_degrades_gracefully_on_a_malformed_plan():
    # the reviewer's scenario: a bool where a dict was documented reaches the whole screen
    v = screen({"intent": "edit a gene", "gene": "TP53", "germline": True})
    assert v["decision"] in ("allow", "flag_for_review", "refuse")
