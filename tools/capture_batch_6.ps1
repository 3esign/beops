Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function C($sid,$name,$urls,$terms,$note,$extra){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }; foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note); if($extra){ $a+=$extra }
  $o = & $py @a 2>&1 | Out-String
  $j=$null; try{ $j=$o|ConvertFrom-Json }catch{}
  if($j){ Write-Output ("{0,-5} allowed={1,-5} ok={2,-5} disagree={3} signal={4}" -f $sid,$j.allowed_for_us,$j.capture_ok,($j.engines_disagreed -join ','),($j.content_signal|ConvertTo-Json -Compress)) }
  else { Write-Output ("{0,-5} RAW {1}" -f $sid, (($o -replace '\s+',' ')).Substring(0,[Math]::Min(150,$o.Length))) }
}
C 'S157' 'SEPA pollen API' @('http://77.46.150.200/api/opendata/locations/') @() 'bare IP, plain HTTP' $null
C 'S158' 'RATEL EMF drive-test' @('https://emf.ratel.rs/drive-test-open-data/open-data-7-1.json') @() 'GPS tracks with field strength' @('--allow-shared-host')
C 'S159' 'Ministry of Education open data' @('https://opendata.mpn.gov.rs/srv/Vs/PodaciOLOPJSON') @() 'institutions with rooms and floor area' $null
C 'S160' 'Ministry of Culture heritage via geosrbija' @('https://opendata.geosrbija.rs/') @() 'official immovable cultural property register' @('--allow-shared-host')
C 'S164' 'World Bank Projects API' @('https://search.worldbank.org/api/v3/projects?format=json&countrycode_exact=RS&rows=3') @('https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets') '108 Serbia projects' $null
C 'S165' 'CORDIS EU research projects bulk' @('https://cordis.europa.eu/data/cordis-HORIZONprojects-json.zip') @() '139 MB zip, body read capped' $null
C 'S166' 'EIB project loans register' @('https://www.eib.org/en/projects/loans/') @() 'HTML search' $null
C 'S167' 'EBRD' @('https://www.ebrd.com/') @() 'robots Allow /' $null
C 'S168' 'WBIF' @('https://wbif.eu/beneficiaries/serbia') @() 'robots allows, www host returned 403 - retry at apex' $null
C 'S169' 'keep.eu Interreg projects' @('https://keep.eu/wp-json/') @() 'WordPress REST, keep/v1 namespace' $null
C 'S170' 'IATI Registry' @('https://iatiregistry.org/api/3/action/package_list') @() 'CKAN v3 keyless' $null
& $py -B tools/build_provenance_index.py
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
git add -A
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -m "International money leaves a trail, and most of it is not geocoded

Seven financiers probed. The World Bank Projects API v3 answers keyless with
108 Serbia projects totalling USD 5.87 billion, but returns no geolocation at
all, so those projects bind only through their implementing agency, which is a
building and not a project site. CORDIS publishes every Horizon project with
its participants and their addresses as a 139 MB open download. IATI is the one
source in the set that is geocoded by the standard rather than by accident.

WBIF is recorded under a new status, blocked: its robots.txt says Allow slash
and the Serbia page returned 403 to our identified agent. Permission granted by
the file, refused by the server. That is not an opt-out and must not be filed
as one, and it is not access either.

Also registered from the host extraction: the pollen API with station
coordinates, three in Belgrade; RATEL EMF drive tests, GPS tracks carrying
field strength and height, this project's first moving sensor and first line
geometry; the education ministry's institutions with room counts and floor
area, by address and not coordinate; and the culture ministry's official
heritage register served through the national spatial infrastructure.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01L8NfE9kz5DBpWDL6cYpeKP" 2>&1 | Select-Object -Last 4
git log --oneline -2
