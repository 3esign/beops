# Shared BEOPS scheduled-task definition. Dot-source this file from scripts that
# need the canonical clock list; do not copy the table.
$script:BeopsTasksToolsRoot = Split-Path -Parent $PSCommandPath

function Get-BeopsRoot {
  return (Resolve-Path (Join-Path $script:BeopsTasksToolsRoot '..')).Path
}

function Get-BeopsTaskSpecs {
  return @(
    [pscustomobject]@{ Name='Beops_Collect';  Bat='tools\collect_tick.bat';  Minutes=5;     Limit=10; Desc='BEOPS: one bounded pass over permitted sources' },
    [pscustomobject]@{ Name='Beops_Organ';    Bat='tools\organ_tick.bat';    Minutes=10;    Limit=9;  Desc='BEOPS: one bounded pass of the news-sorter organ on a local model' },
    [pscustomobject]@{ Name='Beops_Publish';  Bat='tools\publish_tick.bat';  Minutes=10;    Limit=8;  Desc='BEOPS: export and push the public site (github.com/3esign/beops)' },
    [pscustomobject]@{ Name='Beops_Mind';     Bat='tools\mind_tick.bat';     Minutes=4;     Limit=12; Desc='BEOPS: one drop of the mind - one step of the endless conversation on local models' },
    [pscustomobject]@{ Name='Beops_Watch';    Bat='tools\watch_tick.bat';    Minutes=10;    Limit=5;  Desc='BEOPS: the watchman - reads artefacts, never task status as truth' },
    [pscustomobject]@{ Name='Beops_Legal';    Bat='tools\legal_tick.bat';    Minutes=10080; Limit=30; Desc='BEOPS: weekly re-capture of the permission evidence of every polled source' },
    [pscustomobject]@{ Name='Beops_Guard';    Bat='tools\guard_tick.bat';    Minutes=15;    Limit=20; Desc='BEOPS: guard - checks task liveness, permissions, organs and publish gate' },
    [pscustomobject]@{ Name='Beops_Baseline'; Bat='tools\baseline_tick.bat'; Minutes=60;    Limit=60; Desc='BEOPS: hourly baseline build for transport and static comparison layers' }
  )
}
