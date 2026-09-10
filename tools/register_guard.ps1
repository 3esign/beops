# Registers only Beops_Guard through the central task registry.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'register_tasks.ps1') -Only Beops_Guard
