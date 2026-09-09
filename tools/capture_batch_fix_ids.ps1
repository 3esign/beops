Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function Cap($sid,$name,$urls,$terms,$note,$extra){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }
  foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note); if($extra){ $a+=$extra }
  Write-Output ("===== "+$sid); & $py @a 2>&1 | Select-Object -Last 30
}
Cap 'S57' 'JP Putevi Srbije - annual AADT (PGDS) per road section' `
  @('https://www.putevi-srbije.rs/images/pdf/brojanje/2023/DP-IA-PGDS-2023-eng.xls','https://www.putevi-srbije.rs/') @() `
  'was mistakenly captured as S134; correct id is S57. 86 files verified, 2018-2024, Remark column labels ATC/TS/INT' $null
Cap 'S95' 'Overture Maps Foundation - open global map data' `
  @('https://docs.overturemaps.org/getting-data/') @('https://docs.overturemaps.org/attribution/') `
  'was mistakenly captured as S136; correct id is S95' @('--allow-shared-host')
Cap 'S04' 'Sensor.Community - citizen air quality and noise sensors' `
  @('https://data.sensor.community/static/v2/data.json','https://maps.sensor.community/') @('https://sensor.community/en/') `
  'was mistakenly captured as S137; correct id is S04' @('--allow-shared-host')
Write-Output "===== now re-run the duplicates to prove the guard works"
& $py -B tools/legal_capture.py --sid S134 --name 'duplicate probe' --url 'https://www.putevi-srbije.rs/' --note 'expect refusal' 2>&1 | Select-Object -Last 10
