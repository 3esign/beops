# BEOPS operational order - 2026-09-11

Status: current
Scope: repository/order, not a scientific result about Belgrade

## Folder roles

- `!Projekti/Beops` is the active private working repository. This is where research, collectors, evidence, runtime scripts and local traces live.
- `!Projekti/Beops-public` is the public mirror. It is populated by `tools/publish_github.ps1` and pushed to `https://github.com/3esign/beops.git`.
- A workspace organizer must skip Beops unless the requested task is explicitly Beops work. This is an active scientific instrument, not an archive pile.

## C/D path rule

Both `C:\Svemir\!Projekti\Beops` and `D:\Svemir\!Projekti\Beops` can appear because the Svemir workspace uses entry points/junctions. Scripts must not encode either one as the truth. Operational scripts resolve the project from their own location with `%~dp0..` or `$PSScriptRoot`.

The one exception is runtime discovery of the currently available Python command. `tools/beops_env.bat` centralizes that choice for batch ticks. PowerShell publishing uses the same idea and allows `BEOPS_PYTHON`, `BEOPS_TEST_PYTHON` and `BEOPS_PUBLIC_ROOT` overrides.

## Current scheduled clocks

The canonical scheduler definition is `tools/register_tasks.ps1`. It registers:

- `Beops_Collect` every 5 minutes
- `Beops_Mind` every 4 minutes
- `Beops_Organ` every 10 minutes
- `Beops_Publish` every 10 minutes
- `Beops_Watch` every 10 minutes
- `Beops_Legal` every 10080 minutes
- `Beops_Guard` every 15 minutes
- `Beops_Baseline` every 60 minutes

Single-task wrappers call the same registry with `-Only`, so they cannot drift into different actions, roots or settings.

## Publish safety

The publish lock lives in `runtime/publish.lock`, not `data/live`. It coordinates local execution and is not city data.

The public mirror is cleared and copied only after the publish gate passes. A failing test suite must leave the existing public mirror intact and write a receipt the guard can read.

## Remaining known disorder

- The project still uses two Python capabilities in practice: collection/build scripts prefer `C:\Svemir\python.cmd` when present, while the test gate can require the bundled Codex Python because of local package availability. This is now explicit, not solved.
- Legacy one-shot probe, capture and commit helper scripts from earlier waves still contain hardcoded `D:\Svemir\!Projekti\Beops` paths. They are not canonical scheduler actions. Change them only when a new wave needs to reuse them, because some are historical trail helpers.
- The source repository has generated dirty files from live clocks. They are data movement, not part of this operational cleanup, and must not be reverted casually.
- Full `npm test` can mutate generated public/live artifacts. Use targeted tests for operational changes unless the goal is a full regeneration wave.
