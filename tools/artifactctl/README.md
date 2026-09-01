# artifactctl

`artifactctl` tracks exact local files under explicit workflow run IDs. It does
not scan for deletion candidates and it never modifies remote pCloud, Google
Drive, or FlatFilePro data.

```bash
tools/artifactctl/artifactctl run start --owner report-fetcher --client acme --workflow amazon-reporting
tools/artifactctl/artifactctl register --run RUN_ID --path output/acme/reporting/report.csv --disposition archive-pcloud
tools/artifactctl/artifactctl run complete --run RUN_ID --outcome success
tools/artifactctl/artifactctl cleanup --audit-only
tools/artifactctl/artifactctl quarantine list
tools/artifactctl/artifactctl quarantine restore --artifact ARTIFACT_ID
```

Successful runs become eligible after seven days. Eligible exact files enter a
30-day local quarantine only after their disposition-specific verification.
Changed, missing, unregistered, manually supplied, failed-run, and out-of-scope
files are preserved. Purge unlinks one verified quarantine file at a time.
