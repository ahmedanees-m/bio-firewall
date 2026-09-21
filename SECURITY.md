# Security policy

BioFirewall is a design-stage screen for genome-writing plans. It is a research prototype and a
reference implementation, not an operational control. This file states how to report a weakness and
what the implementation does and does not guarantee.

## Reporting

Report suspected vulnerabilities privately through GitHub's
[security advisory form](https://github.com/ahmedanees-m/bio-firewall/security/advisories/new)
rather than by opening a public issue.

Please include the version or commit, the configuration, and the smallest input that shows the
behaviour. An acknowledgement should be expected within fourteen days. We ask for ninety days before
public disclosure, and will agree a shorter window where a weakness is already public or a longer one
where a fix needs coordination.

For a finding that could assist misuse rather than only affect the software, describe the property
that fails and withhold a working construction until a fix is available.

## Scope

In scope: the screening path, the design passport, the managed-access plane, the audit log, the
reference adapters, and the evaluation code.

Out of scope, because they are not evaluated here: upstream parsing and construction of the
structured plan, adapter implementations other than the two reference ones, policy configuration
loading, downstream execution of a released plan, the host application, and the human review step a
flagged plan routes into.

## What the implementation guarantees, and under what assumptions

These are properties of the implementation as tested. They are not deployment guarantees, and each
depends on the trusted computing base below.

**Screening reads a structured plan, not free text.** A submitted artefact is projected onto the
five screened axes before any rule runs, so text outside that projection does not reach a hazard
axis. Invariance to injected text follows by construction. It evidences a design property and is not
a claim that the end-to-end chain resists an adversary.

**The passport binds the plan it was issued for.** Mutation of a signed field is detected, and a
passport does not carry across to a materially different design.

**A withheld access resolution withholds execution**, including where the screen decision alone
would have released the plan.

**Verification returns a verdict rather than raising**, so a failed check cannot escape a gate as an
exception.

## Deployment obligations

Three things are the deployer's responsibility, and the defaults are not sufficient for deployment.

**Set `BIOFW_PASSPORT_KEY`.** Without it the package signs under a published default key, and a
passport minted under that default is not authenticated: anyone holding the source can produce one.
A passport signed under the default carries `dev_key: true` inside its signed body, so a verifier can
refuse it. Do not accept a `dev_key` passport as evidence that a plan was screened.

**Configure the audit log, and anchor it.** Logging is opt-in, and the record is held in memory
unless a path is given, so an unconfigured deployment produces no audit record. Unkeyed, the chain
detects accidental corruption and modification by a party who does not recompute it; it does not
detect modification by a party who can write to the store, because an unkeyed digest needs no secret.
Set `BIOFW_AUDIT_KEY` to chain under HMAC. Separately, every prefix of a valid chain is itself valid,
so detecting a removed tail requires retaining the head digest and entry count outside the log and
passing them to `verify()`.

**Keep the vendored hazard tables intact.** A rule whose table is absent stops matching rather than
failing. `missing_vendored()` reports which are absent, a verdict produced by a partial install
carries `degraded_resources`, and `BIOFW_REQUIRE_VENDORED_DATA=1` makes the condition fatal.

## Trusted computing base

Any guarantee above rests on the integrity of the installed package and its dependencies, the
vendored hazard tables, the host operating system and Python runtime, the deployment key, the audit
store, and the human reviewer to whom a flagged plan is routed.

## Known limitations

- The screen is deterministic, locally installed and unmetered, which makes repeated querying to
  search for a passing variant inexpensive. The session monitor addresses modelled decomposition
  across a session, not query-based search, and is opt-in.
- The passport carries no expiry or nonce, so a valid passport re-verifies indefinitely.
- Audit entries carry no timestamp, so the record orders decisions relative to one another and not
  against any clock.
- The hazard axes are evaluated on safe public proxies and have not been exercised against an agent
  of concern.
