# Security and Dependency Management

This service uses Poetry (`pyproject.toml` + `poetry.lock`) to pin and reproduce production dependencies.

## Routine dependency maintenance

- Update dependencies: `make update`
- Run tests: `make test`
- Run vulnerability audit (requires network access): `make audit` (audits the installed env after syncing to `poetry.lock`)

## Production guidance

- Keep `poetry.lock` committed and in sync with `pyproject.toml`.
- Rebuild and redeploy after dependency or base image updates.
