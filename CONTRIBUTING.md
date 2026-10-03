# Contributing

Use one GitHub issue per implementation unit.

Create a feature branch from main, implement the change within the existing modular boundaries, add tests, and verify:

```bash
conda activate ani-watch
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Open a pull request for review. Keep commits focused and avoid unrelated changes.

Do not commit Conda environments, credentials, tokens, caches, local databases, generated build output or private media.
