Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function C($sid,$name,$url,$note){
  $o = & $py -B tools/legal_capture.py --sid $sid --name $name --url $url --note $note --allow-shared-host 2>&1 | Out-String
  $j=$null; try{ $j=$o|ConvertFrom-Json }catch{}
  if($j){ Write-Output ("{0,-6} allowed={1,-6} ok={2,-6} trust={3} disagree={4}" -f $sid,$j.allowed_for_us,$j.capture_ok,$j.tls_trust,($j.engines_disagreed -join ',')) }
  else  { Write-Output ("{0,-6} RAW {1}" -f $sid, (($o -replace '\s+',' ')).Substring(0,[Math]::Min(140,$o.Length))) }
}
C 'S10'  'Parking servis free spaces' 'https://www.parking-servis.co.rs/lat/garaze-i-parkiralista' 're-capture with the machine trust store'
C 'S59'  'RATEL radio-frequency licence register' 'https://registar.ratel.rs/sr/reg203' 're-capture with the machine trust store'
C 'S79'  'GO Vracar news RSS' 'https://vracar.rs/index.php/vesti/feed/' 're-capture'
C 'S149' 'APR company register open API' 'https://openapi.apr.gov.rs/api/opendata/companies' 're-capture, body read is capped'
C 'S156' 'Public Procurement Office - portal notices' 'http://portal.ujn.gov.rs/OpenD/OpenData_2020.xlsx' 're-capture'
C 'S162' 'Ministry of Justice - court statistics' 'http://opendata.ite.gov.rs/api/data/mpravde/ODV2019MSP.xlsx' 're-capture'
C 'S42'  'Public Procurement Portal (UJN)' 'https://jnportal.ujn.gov.rs/' 're-capture: Allow: /$ - urllib mishandles the $ anchor, engines now disagree rather than silently refusing'
& $py -B tools/build_provenance_index.py
