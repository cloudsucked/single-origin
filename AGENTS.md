# Agents Notes

- On this GitLab server, do not define pipeline jobs using standard `image:` container jobs.
- CI must be implemented via approved Backstage/GitLab CI components (for example `cloudflare/ci/...` includes).
- When adding or updating `.gitlab-ci.yml`, use component includes and component inputs only.
