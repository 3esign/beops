$ErrorActionPreference='Continue'
Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function Cap($sid,$name,$urls,$terms,$note){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }
  foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note)
  Write-Output ("===== "+$sid+" "+$name)
  & $py @a 2>&1 | Select-Object -Last 40
}
Cap 'S134' 'Putevi Srbije - annual AADT (PGDS) per road section' `
  @('https://www.putevi-srbije.rs/images/pdf/brojanje/2023/DP-IA-PGDS-2023-eng.xls','https://www.putevi-srbije.rs/') `
  @('https://www.putevi-srbije.rs/index.php/sr/') `
  'XLS+PDF per road category IA/IB/IIA/IIB, 2018-2024, 86 files verified present; Remark column labels each row ATC/TS/INT'
Cap 'S135' 'gisportal.rs ArcGIS Server (JP Putevi Srbije GDi Smart Portal)' `
  @('https://gisportal.rs/server/rest/services?f=pjson','https://gisportal.rs/server/rest/services/ITS_Putevi_Srbije?f=pjson') `
  @() `
  'root service listing is public; every folder returns 499 Token Required - closed, name known, no token sought'
Cap 'S136' 'Overture Maps Foundation - open global map data' `
  @('https://docs.overturemaps.org/getting-data/') `
  @('https://docs.overturemaps.org/attribution/') `
  'keyless S3/Azure parquet; release 2026-08-19.0; theme licences differ (ODbL vs CDLA)'
Cap 'S137' 'Sensor.Community - citizen air quality and noise sensors' `
  @('https://data.sensor.community/static/v2/data.json','https://maps.sensor.community/') `
  @('https://sensor.community/en/') `
  'keyless JSON of last 5 minutes across the network; check Belgrade node count'
Cap 'S138' 'UNESCO World Heritage Centre - list and tentative list' `
  @('https://whc.unesco.org/en/list/xml/','https://whc.unesco.org/en/statesparties/rs') `
  @('https://whc.unesco.org/en/disclaimer/') `
  'machine-readable XML of the whole list; Serbia has 5 inscribed, 12 tentative, none in Belgrade'
Cap 'S139' 'ISRBC Sava Commission - Sava GIS / Sava HIS' `
  @('https://www.savacommission.org/') `
  @('https://www.savacommission.org/UserDocsImages/05_documents_publications/basic_documents/savagis_datapolicy_v1.0_and_annexes_final.pdf') `
  'data policy: download requires registration AND forbids redistribution to third parties without consent - incompatible with publishing evidence'
Cap 'S140' 'ICPDR Danube River Basin Water Quality Database (TNMN)' `
  @('https://wq-db.icpdr.org/') `
  @('https://www.icpdr.org/tasks-topics/topics/water-quality/transnational-monitoring-network') `
  'registration via Danubis required; 79 TNMN monitoring locations basin-wide'
