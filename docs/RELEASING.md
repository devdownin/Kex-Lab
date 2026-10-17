# Releasing the Lab bundle

`VERSION` is the Lab bundle version; `versions.env` records the component images.
The first bundle is **0.1.0**. Component versions remain independent.

## Prepare a reviewable candidate

1. Update `VERSION`, `CHANGELOG.md` and `docs/releases/v<VERSION>.md` together.
2. Run `make check`, `make integration-smoke` and `make observability-smoke`.
3. Commit the reviewed files and run `make release-prepare` from a clean worktree.
4. Verify the assets with `(cd dist && sha256sum -c SHA256SUMS)`.

The preparation command reads the exact committed source through Git, includes
its SHA in `bundle.json`/notes and creates a reproducible source archive.
Credentials, generated reports, component checkouts and models are excluded.
The output contains:

- `kex-lab-0.1.0.tar.gz`: source, configuration, docs and scripts from that commit;
- `versions.env`: component compatibility manifest;
- `bundle.json`: bundle version, source SHA, commit date and image references;
- `release-notes.md`: human-readable notes with the exact image set;
- `SHA256SUMS`: hashes for the four files above.

Preparation does not create a Git tag or publish a GitHub release. CI uploads
the same exact-head assets as `kex-lab-release-candidate` on the PR validation
run so they can be downloaded and reviewed before publishing.

## Publish after merging

Use the reviewed `main` commit with passing checks. Confirm that its `VERSION`
and release notes match the intended version, then create and push the matching
annotated tag, for example `v0.1.0`. Do not tag an unmerged feature commit.

The release workflow fetches main history, verifies the tagged commit is an
ancestor of main and that the tag matches `VERSION`, reruns repository checks,
Kafka integration and observability smoke, and builds/checksums the exact source.
Only then does it create the GitHub release with the archive, manifest and hashes.
A failed check prevents publication.

A manual workflow run on a main-history commit builds and uploads a candidate
artifact without publishing. Publish only after the candidate is reviewed and its feature PR is merged.
