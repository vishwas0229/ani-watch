# Contributing to Ani-Watch

1. Create a feature branch from `main`.
2. Implement one cohesive change with tests.
3. Run:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

4. Open a pull request and describe the affected issue(s).
5. Keep provider, storage, metadata, and player integrations behind their existing interfaces.

For local development, use the project Conda environment from `environment.yml`.
