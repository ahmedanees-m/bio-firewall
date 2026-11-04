"""Ordinary research phrasing must not hard-reject.

Two rules previously fired on free prose: the bare staphylococcal abbreviations `sea`, `sec`, `sed` and
`see` are ordinary English words, and the oncogene-activation rule matched `activate` inside `inactivate`
with no direction check. The screen reaches these through `screen_cargo`'s fallback to `plan["intent"]`
when a plan declares no cargo function, so the suite pins the benign side as well as the hazardous one."""
from __future__ import annotations

import pytest

from bio_firewall import screen

BENIGN = [
    "to see the effect of the edit on expression",
    "sea urchin embryos as a comparative model",
    "image at 10 sec intervals",
    "inactivate the MYC oncogene",
    "CRISPRi silencing of the MYC oncogene promoter",
    "knockout of the MYC oncogene for cancer modelling",
    "disrupt the MYC oncogene promoter region",
    "loss-of-function screen across the MYC oncogene locus",
]

HAZARD = [
    ("activate the MYC oncogene via enhancer insertion", "MYC"),
    ("insert an enhancer to drive the LMO2 oncogene", "LMO2"),
    ("overexpression of the MYC oncogene by promoter insertion", "MYC"),
    ("express staphylococcal enterotoxin B", "AAVS1"),
    ("express enterotoxin SEA in the construct", "AAVS1"),
    ("cargo encodes ricin toxin A chain", "AAVS1"),
]


@pytest.mark.parametrize("intent", BENIGN)
def test_ordinary_phrasing_is_not_hard_rejected(intent):
    gene = "MYC" if "MYC" in intent else "TP53"
    v = screen({"intent": intent, "gene": gene})
    assert v["decision"] != "refuse", f"{intent!r} was refused: {v}"


@pytest.mark.parametrize("intent,gene", HAZARD)
def test_designed_activation_and_listed_toxins_still_refuse(intent, gene):
    v = screen({"intent": intent, "gene": gene})
    assert v["decision"] == "refuse", f"{intent!r} was not refused: {v}"
