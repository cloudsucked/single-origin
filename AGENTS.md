# Agents Notes

- On this GitLab server, do not define pipeline jobs using standard `image:` container jobs.
- CI must be implemented via approved Backstage/GitLab CI components (for example `cloudflare/ci/...` includes).
- When adding or updating `.gitlab-ci.yml`, use component includes and component inputs only.

## Deployment — push to GitHub after every merge to main

The CML `generic-origin` infrastructure template provisions lab VMs by cloning from the **GitHub mirror** (`github` remote), not from GitLab. Changes merged to `main` on GitLab will not appear in new lab pods until they are also pushed to GitHub.

After every merge to `main`, always run:

```bash
git push github main
```

Both remotes are already configured:
- `origin` → `git@gitlab.cfdata.org:cloudflare/sxp/single-origin.git` (source of truth, CI runs here)
- `github` → `git@github.com:cloudsucked/single-origin.git` (read by CML at pod creation time)

**Never push directly to `github` without first merging to `origin/main`.**
If you are unsure whether the GitHub remote is up to date, run `git fetch github && git log github/main..main` to see what is missing.
