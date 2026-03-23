# Security

## Reporting issues

Please use [GitHub **Security** advisories](https://github.com/MatthewEngman/telos-framework/security/advisories/new) (**Report a vulnerability**) for sensitive reports instead of public issues.

## Expression evaluation (canonical MILP + memory)

**Design intent:** replace arbitrary `eval` with a **small safe expression engine for linear MILP expressions**, and a **separately scoped safe evaluator for memory updates** (scalar `max`/`min` and arithmetic).

**Linearity invariant:** every accepted MILP expression must be **linear with respect to decision variables** (no products of two decision-bearing terms; division only when the denominator is decision-free). That rule is enforced in `telos.linear_milp` and covered by corpus + fuzz tests.

**MILP objectives and invariants** (`.telos` / `TelosSchema`, canvas router+hardware JSON) are compiled with a **purpose-built linear expression engine** (`telos.linear_milp`): numbers, identifiers, `+`, `-`, `*`, `/` (decision-free denominators), parentheses with a **bounded nesting depth** (`telos.expr_limits`), and **linearity** checks (no product of two decision-related PuLP terms). There is **no** Python `eval` on this path.

**Memory `update` strings** (temporal “heat” and similar) use a **separately scoped scalar evaluator** (`telos.memory_expr`): `+`, `-`, `*` (no `/` yet), bounded **parenthesis nesting**, identifiers as floats, and **whitelisted** `max(...)` / `min(...)`—again **no** `eval`.

**Still treat as trusted input** for policy and correctness: manifests and WebSocket payloads define your optimization geometry. Only load `.telos` and canvas JSON from sources you trust, validate changes in review, and do not expose an unauthenticated “upload a manifest” endpoint to the internet without additional controls. Parser bugs or future grammar extensions remain an attack surface to test and harden.

## Experimental TIR path (`main.py`, `telos.tir_compiler`)

Continuous-mode demos parse expressions with **SymPy `sympify`**. That path is separate from the MILP engine; treat TIR JSON from LLMs or users as **trusted** until you constrain or replace `sympify` with a tighter grammar.

## Other practices

- Never commit API keys. Use environment variables (`OPENAI_API_KEY`) and CI secrets only.

## Roadmap

- Corpus tests keep **checked-in manifests** compatible with the parsers; Hypothesis fuzz tests (dev extra) assert **no crash** and a **per-example time budget** on random strings.
- Extend the MILP grammar only with explicit security review and the linearity invariant above.
- TIR: tighten `sympify` only when that path crosses an untrusted boundary (see previous section).
