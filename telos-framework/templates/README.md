# Curated templates

Approved community templates live here as `.telos` files. They are the **source of truth** for the public catalog; the Lovable actuator hub can fetch [`index.json`](index.json) once the site is published. CI **verifies** that `index.json` matches the generator output (it does not commit to `main` when branch rules require pull requests).

## Submitting a template

1. Open **[Submit a template](https://github.com/MatthewEngman/telos-framework/issues/new/choose)** (or your repo’s equivalent) and paste a valid manifest plus optional `template:` metadata.
2. After maintainers review, a pull request adds the file under `templates/` and updates `index.json` (see **Local checks**).
3. **Templates catalog** workflow on pushes and PRs fails if `index.json` is out of date relative to the generator.

Optional root `template:` block (see `telos.models.TelosTemplate`): `name`, `category`, `author`, `description`, `actuators`.

## Local checks

```bash
cd telos-framework
python -m pip install -e ".[dev]"
python -m telos validate templates/your_file.telos
python scripts/generate_templates_index.py
```

Always commit `templates/index.json` together with template changes so CI passes.

## Branch protection

If `main` requires pull requests, the catalog workflow cannot push fixes for you; run `generate_templates_index.py` before merge and include the updated `index.json` in the PR.
