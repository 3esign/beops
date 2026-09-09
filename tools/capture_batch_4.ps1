Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function C($sid,$name,$urls,$terms,$note,$extra){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }; foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note); if($extra){ $a+=$extra }
  $o = & $py @a 2>&1 | Out-String
  $j=$null; try{ $j=$o|ConvertFrom-Json }catch{}
  if($j){ Write-Output ("{0,-5} allowed={1,-5} ok={2,-5} disagree={3} signal={4}" -f $sid,$j.allowed_for_us,$j.capture_ok,($j.engines_disagreed -join ','),($j.content_signal|ConvertTo-Json -Compress)) }
  else { Write-Output ("{0,-5} RAW {1}" -f $sid, (($o -replace '\s+',' ')).Substring(0,[Math]::Min(160,$o.Length))) }
}
C 'S146' 'SEPA air quality HVD API (opendata.kosava.cloud)' @('http://opendata.kosava.cloud/api/v1/metadata','http://opendata.kosava.cloud/api/v1/stations','http://opendata.kosava.cloud/api/v1/observations') @('http://opendata.kosava.cloud/legal/license','http://opendata.kosava.cloud/legal/terms') 'HVD under Reg (EU) 2023/138, cited by the source as an ELI URI' $null
C 'S147' 'data.gov.rs national open data portal' @('https://data.gov.rs/api/1/datasets/','https://data.gov.rs/api/1/site/') @('https://data.gov.rs/sr/licences/') 'udata API, 3530 datasets harvested' $null
C 'S148' 'RZS open data REST' @('https://opendata.stat.gov.rs/data/WcfJsonRestService.Service1.svc/dataset/220205IND02/1/json') @() 'robots.txt: User-agent * Allow /' $null
C 'S149' 'APR company register open API' @('https://openapi.apr.gov.rs/api/opendata/companies') @() 'monthly snapshot with DatumPreseka' $null
C 'S150' 'RGZ Address Register via geosrbija download API' @('https://download.geosrbija.rs/download-api/opendata-proxy/export?category=ar&layer=ulica_ar&geometry=true&fileName=ulica_csv&format=csv') @() 'GeoPackage and CSV, keyless' $null
C 'S151' 'Ministry of Mining CISGIR OpenData ArcGIS' @('http://gis.mre.gov.rs/arcgis/rest/services/OpenData/CISGIR/MapServer?f=pjson') @() 'open ArcGIS, three polygon layers' $null
C 'S152' 'SEPA airborne pollen' @('https://data.gov.rs/sr/datasets/polen-objedinjeni-podatsi-od-2016-godine/') @() 'weekly, 32MB combined since 2016' @('--allow-shared-host')
C 'S153' 'SEPA NRIZ emissions to air' @('https://data.gov.rs/sr/datasets/emisije-u-vazdukh/') @() 'annual 2010-2024' @('--allow-shared-host')
C 'S154' 'Commissioner for Information of Public Importance - daily data' @('https://data.gov.rs/api/1/datasets/?q=%D0%9F%D0%BE%D0%B2%D0%B5%D1%80%D0%B5%D0%BD%D0%B8%D0%BA') @() '16 daily CSV series' @('--allow-shared-host')
C 'S155' 'RATEL spectrum and internet speeds' @('https://www.nettest.ratel.rs/opendata','http://registar.ratel.rs/cyr/reg204') @() 'spectrum daily, speeds continuous' $null
C 'S156' 'Public Procurement Office - portal notices' @('http://portal.ujn.gov.rs/OpenD/OpenData_2020.xlsx') @() '2013 onward, plain http' $null
& $py -B tools/build_provenance_index.py
