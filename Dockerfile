# BioFirewall - reproducible container image.
#
# Pins Python 3.11 and installs the package (which pulls pen-stack>=0.1.0,<0.2.0 from PyPI, resolving the current
# in-range release). The image is self-contained: the five-axis screen, the signed hazard KB, and the vendored
# open data all ship inside the wheel, so `screen()`, the demo, and the committed-data reproduction run with no
# external data or network.
#
#   docker build -t biofirewall .
#   docker run --rm biofirewall                 # runs examples/demo.py (the default)
#   docker run --rm biofirewall make reproduce  # committed-data headline numbers + full test suite
#   docker run --rm biofirewall make test       # the full unit suite
#   docker run --rm -it biofirewall bash        # an interactive shell
#
# The reconcile end-to-end path additionally needs a pen-stack source checkout mounted at PEN_STACK_HOME; the
# committed-data results and the rest of the suite do not. See REPRODUCTION.md.

FROM python:3.11-slim

# A writable path for the PEN-STACK Guardian's audit log (matches the CI environment).
ENV PEN_STACK_SAFETY_AUDIT=/tmp/bf_safety_audit.log \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Build tooling for the (few) source wheels in the dependency tree.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/bio-firewall

# Install dependencies first (better layer caching), then the package with its dev extras (pytest + ruff),
# so the container can run the full reproduction out of the box.
COPY pyproject.toml README.md ./
COPY bio_firewall ./bio_firewall
COPY tests ./tests
COPY examples ./examples
COPY data ./data
COPY results ./results
COPY standards ./standards
COPY prereg ./prereg
COPY tools ./tools
COPY Makefile locus_mouse_outcome_validation.py ./

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]"

# Smoke-test the install at build time so a broken image fails the build, not the user.
RUN python -c "from bio_firewall import screen; assert screen({'edit': {'fusion_genes': ['BCR','ABL1']}})['decision'] == 'refuse'" \
    && python -c "from bio_firewall.kb import load_kb, verify_kb; assert verify_kb(load_kb())"

CMD ["python", "examples/demo.py"]
