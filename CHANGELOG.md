# Changelog

All notable changes to Kex Lab are documented here. Kex Lab releases describe the compatible integration bundle; individual components keep their own release lifecycle.

## Unreleased

### Added
- Task-grouped `make help` as the default command, with a CLI walkthrough.
- Actionable, read-only preflight checks for tools, Docker resources, configuration and demo ports; credential values remain hidden.
- Five-step lightweight demo with elapsed time, live progress, concise failure diagnostics, `--verbose` logs and discovered interface URLs.

### Changed
- Readiness retries show elapsed time and final diagnostic details; verbose mode shows every probe.
- The isolated Kafka integration smoke now exercises the public lightweight demo before the DLT assertion.

## 0.1.0 — 2026-10-17

### Added
- Provisioned integrated Grafana dashboard, authenticated Agent metrics scrape and an internal, pinned Python-standard-library adapter for measured AutoTune lag.
- Editable SVG/Mermaid architecture overviews alongside the original PNG.
- `make demo-lite` runs the guided four-service demo without Spectra model downloads and records its evidence.
- Timestamped scenario evidence and Markdown/JSON reports with actual runtime image identities, registry digests, interface links and fail-visible status.
- Versioned, exact-commit release bundles with checksums and a main/tag/checks-gated publication workflow for 0.1.0.
- Shared architecture graphic in the README, architecture guide and end-to-end walkthrough, with descriptive alternative text and explicit optional-integration boundaries.
- `make check` runs repository tests, shell syntax, source links and six Compose profile validations through the same entry point in CI.
- Profile-aware health, smoke and readiness checks with nonzero exit status for missing or unhealthy expected services.
- Unique integration-test Compose projects with ephemeral loopback ports and cleanup restricted to their own resources.
- Exact per-run, per-partition offset assertions and DLT checks restricted to newly produced records.
- Immutable Docker Hub index digests for AutoTune and both Spectra images, resolved on 2026-10-17 and shared with Compose fallbacks.
- One-command `make demo` journey using published Docker Hub images.
- Usage profiles for core, AI, full-stack and guided demo paths.
- Lab health dashboard and reproducible operational scenario catalog.
- Cross-component integration smoke test in GitHub Actions.
- Explicit runtime architecture and integration boundaries.
- Compatibility manifest in `versions.env`.
- Optional operational review profile for compatible KafkaExplorer and Kex-anHarness images: single-broker `lab` topic policy, declared demo DLT source, and persisted lag baselines. The Agent end-to-end check now uses its current authenticated chat API and checks a real MCP tool invocation.

### Fixed
- Probe Explorer liveness directly on loopback so container proxy settings cannot redirect the health check.
- Preserve exported configuration overrides across Lab scripts; load the image manifest for health and runtime commands.
- Keep scenario-specific traffic defaults despite the example `.env`, honor custom topic/partition settings, and use custom counts in assertions.
- Stop the guided demo on readiness failure; allow readiness checks from any working directory and validate retry arguments.
- Pass Make scenario selections correctly and apply local `.env` settings to Compose commands.
- Align setup, Spectra, observability and validation documentation with the implemented workflows; run shell regression contracts in CI.

### Changed
- Update Kex-anHarness names, source links and component checkout paths after the GitHub repository rename; retain the existing Docker image references.
- Pin the published KafkaExplorer `2.1.1` and Kex-anHarness `0.9.16` Docker Hub tags in the compatibility manifest and Compose defaults for the operational review profile.

### Release process
A Kex Lab release is created from a `vX.Y.Z` tag. The release workflow validates the compatibility manifest and publishes release notes containing the exact component image references from `versions.env`.
