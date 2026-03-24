# Curated templates

Approved community templates live here as `.telos` files. They are the **source of truth** for the public catalog; the Lovable actuator hub can fetch [`index.json`](index.json) (regenerated in CI) once the site is published.

## Submitting a template

1. Open **[Submit a template](https://github.com/MatthewEngman/telos-framework/issues/new/choose)** (or your repo’s equivalent) and paste a valid manifest plus optional `template:` metadata.
2. After maintainers review, a pull request adds the file under `templates/`.
3. On merge to `main`, **Templates catalog** workflow validates manifests and refreshes `index.json`.

Optional root `template:` block (see `telos.models.TelosTemplate`): `name`, `category`, `author`, `description`, `actuators`.

## Local checks

```bash
cd telos-framework
python -m pip install -e ".[dev]"
python -m telos validate templates/your_file.telos
python scripts/generate_templates_index.py
```

If `templates/index.json` changes, include it in the same PR, or rely on the post-merge workflow to commit it (when only `.telos` files changed).

## Branch protection

If `main` requires pull requests, the auto-commit job needs a token that can bypass restrictions (for example a PAT with `contents: write`) instead of the default `GITHUB_TOKEN`, or maintainers run `generate_templates_index.py` before merge.
