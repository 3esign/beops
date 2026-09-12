# Shared BEOPS scheduled-task definition. Dot-source this file from scripts that
# need the canonical clock list; do not copy the table.
$script:BeopsTasksToolsRoot = Split-Path -Parent $PSCommandPath

function Get-BeopsRoot {
  return (Resolve-Path (Join-Path $script:BeopsTasksToolsRoot '..')).Path
}

function Get-BeopsTaskSpecs {
  return @(
    # OffsetMinutes spreads the first starts after registration. It does not reduce
    # the sensing or model cadence; it prevents every heavy organ from waking in
    # the same minute on the 8 GB observatory body.
    [pscustomobject]@{ Name='Beops_AIFeed';   Bat='tools\ai_feed_tick.bat';  Minutes=5;     OffsetMinutes=1;  Limit=4;  LogonType='Interactive'; Desc='BEOPS: durable experimental citizen-style AI observations, staggered model cadence within one hour' },
    [pscustomobject]@{ Name='Beops_Collect';  Bat='tools\collect_tick.bat';  Minutes=5;     OffsetMinutes=2;  Limit=10; Desc='BEOPS: one bounded pass over permitted sources' },
    [pscustomobject]@{ Name='Beops_Mind';     Bat='tools\mind_tick.bat';     Minutes=4;     OffsetMinutes=3;  Limit=12; Desc='BEOPS: one drop of the mind - one step of the endless conversation on local models' },
    [pscustomobject]@{ Name='Beops_Organ';    Bat='tools\organ_tick.bat';    Minutes=10;    OffsetMinutes=4;  Limit=9;  Desc='BEOPS: one bounded pass of the news-sorter organ on a local model' },
    [pscustomobject]@{ Name='Beops_Watch';    Bat='tools\watch_tick.bat';    Minutes=10;    OffsetMinutes=8;  Limit=5;  Desc='BEOPS: the watchman - reads artefacts, never task status as truth' },
    [pscustomobject]@{ Name='Beops_Publish';  Bat='tools\publish_tick.bat';  Minutes=30;    OffsetMinutes=10; Limit=8;  Desc='BEOPS: export and push the public site (github.com/3esign/beops)' },
    [pscustomobject]@{ Name='Beops_Guard';    Bat='tools\guard_tick.bat';    Minutes=15;    OffsetMinutes=13; Limit=20; Desc='BEOPS: guard - checks task liveness, permissions, organs and publish gate' },
    [pscustomobject]@{ Name='Beops_Baseline'; Bat='tools\baseline_tick.bat'; Minutes=60;    OffsetMinutes=18; Limit=60; Desc='BEOPS: hourly baseline build for transport and static comparison layers' },
    [pscustomobject]@{ Name='Beops_Legal';    Bat='tools\legal_tick.bat';    Minutes=10080; OffsetMinutes=25; Limit=30; Desc='BEOPS: weekly re-capture of the permission evidence of every polled source' }
  )
}
