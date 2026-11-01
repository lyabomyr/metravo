# Metravo web

Angular app. See the root `README.md` to run it and `docs/CODING_STANDARD.md`
for the structure:

- `src/app/core/` — base classes (`BaseApiService`, `BasePage`), session, config, shared UI
- `src/app/features/<service>/` — one folder per backend service: `*-api.service.ts`, models, pages

The API address comes from `public/runtime-config.json` at runtime, so one
build serves every environment; the deploy workflow overwrites that file.
