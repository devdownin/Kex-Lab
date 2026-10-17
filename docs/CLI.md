# Guided command-line experience

Run `make` or `make help` to choose a task without starting services or creating
configuration. The help groups the main commands into start, test, observe,
diagnose and stop. Run commands from the repository root.

## First run

```sh
make setup
make doctor
make demo-lite
```

`make setup` creates `.env` only if missing. Review it before starting services.
Docker Engine/Desktop, Compose v2, Make, a POSIX shell, curl and Python 3 are
required. A model provider key is needed for actual Agent reasoning, not for
this demo's readiness and Kafka assertions.

## Understand doctor results

`make doctor` does not start, stop or delete services. It uses the effective
settings from `versions.env`, `.env` and exported caller overrides. It checks
the Docker daemon, Compose v2, tools, demo configuration and four published
ports. It reports Docker's allocated CPU/RAM and free space on the checkout
filesystem. For Docker Desktop or remote Docker, also check free space on the
Docker image filesystem: checkout space cannot establish that capacity.

- `OK`: the check passed.
- `WARN`: review the suggested action; the demo can continue. Low resources,
  occupied ports and default local credentials are warnings. A running Lab may
  already own its ports; do not stop unrelated services automatically.
- `ERROR`: correct the suggested issue, then rerun `make doctor`. Missing tools,
  an unreachable daemon, invalid configuration/ports or duplicate host ports
  return exit code 1. Unknown CLI arguments return 2.

The lightweight planning budget is 4 CPUs, 8 GiB RAM and 10 GiB free disk.
Resource warnings are recommendations, not a performance guarantee. Doctor
never prints token values or raw configuration output, including in verbose mode.

## Follow the demonstration

`make demo-lite` runs five numbered steps with elapsed time and a heartbeat
every 10 seconds during long commands:

1. Check prerequisites and show any corrective actions.
2. Start Kafka, Explorer, Agent and AutoTune without seed traffic.
3. Discover their published ports and wait for the `demo` health profile.
4. Inject traffic once and assert the exact Kafka offset increase.
5. Write `reports/latest.md` and `reports/latest.json` with runtime evidence.

The final summary links to the actual Explorer, Agent and AutoTune endpoints,
including ephemeral ports. Open Explorer to inspect `KEX_LAB_TOPIC`, and
AutoTune's dashboard to inspect consumption. The Kafka assertion proves new
records were appended; it does not prove an Agent model/tool invocation.

Grafana is offered as the next optional step via `make observability-up`; the
lightweight demo does not start it. See [observability](OBSERVABILITY.md) for
dashboard authentication, measurements and limits. Stop the lightweight stack
with `make demo-lite-down` to preserve Kafka data.

## Logs and failed runs

```sh
make demo-lite ARGS=--verbose
make doctor ARGS=--verbose
make wait PROFILE=demo ARGS=--verbose
```

Default output summarizes each demo step. A failed step shows the last 40 lines
of its output, its exit code and diagnostic commands; subsequent steps do not
run. Verbose mode streams command output. Long image pulls keep a visible
heartbeat in either mode. Interrupting the demo terminates its current command
but preserves services and data; use `make demo-lite-down` to stop them.

`make wait` prints attempt counts and elapsed time, and shows health details
on the final failure. Verbose mode shows every probe. The existing direct
interface remains available:

```sh
sh scripts/wait-ready.sh 30 5 demo --verbose
```

This means up to 30 probes, with 5 seconds between probes; probe execution time
is additional. Invalid arguments/profile return 2; exhausted readiness attempts
return 1. A failed readiness check suggests `make health PROFILE=demo`, logs
and a verbose retry. `make logs` follows core services; for AutoTune use
`docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml logs autotune`.
