# Registers only Beops_Baseline through the central task registry.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'register_tasks.ps1') -Only Beops_Baseline
