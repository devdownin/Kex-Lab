# Changelog

All notable changes to Kex Lab are documented here. Kex Lab releases describe the compatible integration bundle; individual components keep their own release lifecycle.

## Unreleased

### Added
- One-command `make demo` journey using published Docker Hub images.
- Usage profiles for core, AI, full-stack and guided demo paths.
- Lab health dashboard and reproducible operational scenario catalog.
- Cross-component integration smoke test in GitHub Actions.
- Explicit runtime architecture and integration boundaries.
- Compatibility manifest in `versions.env`.
- Optional operational review profile for compatible KafkaExplorer and Kex Agent AI images: single-broker `lab` topic policy, declared demo DLT source, and persisted lag baselines. The Agent end-to-end check now uses its current authenticated chat API and checks a real MCP tool invocation.

### Release process
A Kex Lab release is created from a `vX.Y.Z` tag. The release workflow validates the compatibility manifest and publishes release notes containing the exact component image references from `versions.env`.
