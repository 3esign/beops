Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function C($sid,$name,$urls,$terms,$note){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }; foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note,'--allow-shared-host')
  $o = & $py @a 2>&1 | Out-String
  $j=$null; try{ $j=$o|ConvertFrom-Json }catch{}
  if($j){ Write-Output ("{0,-5} allowed={1,-5} ok={2,-5} disagree={3} signal={4}" -f $sid,$j.allowed_for_us,$j.capture_ok,($j.engines_disagreed -join ','),($j.content_signal|ConvertTo-Json -Compress)) }
  else { Write-Output ("{0,-5} RAW {1}" -f $sid, (($o -replace '\s+',' ')).Substring(0,[Math]::Min(200,$o.Length))) }
}
C 'S147' 'data.gov.rs national open data portal' @('https://data.gov.rs/api/1/datasets/','https://data.gov.rs/api/1/site/') @() 'udata API, 3530 datasets harvested'
C 'S148' 'RZS open data REST' @('https://opendata.stat.gov.rs/data/WcfJsonRestService.Service1.svc/dataset/220205IND02/1/json') @() 'robots.txt: User-agent * Allow /'
C 'S149' 'APR company register open API' @('https://openapi.apr.gov.rs/api/opendata/companies') @() 'monthly snapshot with DatumPreseka; 57.8 MB, body read capped'
C 'S155' 'RATEL spectrum and internet speeds' @('https://www.nettest.ratel.rs/opendata') @() 'speeds continuous'
C 'S156' 'Public Procurement Office - portal notices' @('http://portal.ujn.gov.rs/OpenD/OpenData_2020.xlsx') @() '2013 onward, plain http'
& $py -B tools/build_provenance_index.py
