Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function C($sid,$name,$urls,$terms,$note,$extra){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }; foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note); if($extra){ $a+=$extra }
  $o = & $py @a 2>&1 | Out-String
  $j = $null; try { $j = $o | ConvertFrom-Json } catch {}
  if($j){ Write-Output ("{0,-5} allowed={1,-5} capture_ok={2,-5} disagree={3} signal={4}" -f $sid, $j.allowed_for_us, $j.capture_ok, ($j.engines_disagreed -join ','), ($j.content_signal | ConvertTo-Json -Compress)) }
  else  { Write-Output ("{0,-5} RAW: {1}" -f $sid, ($o -replace '\s+',' ').Substring(0,[Math]::Min(200,$o.Length))) }
}
C 'S57'  'JP Putevi Srbije - annual AADT (PGDS) per road section' @('https://www.putevi-srbije.rs/images/pdf/brojanje/2023/DP-IA-PGDS-2023-eng.xls','https://www.putevi-srbije.rs/') @() 're-capture through the RFC 9309 engine' $null
C 'S95'  'Overture Maps Foundation' @('https://docs.overturemaps.org/getting-data/') @('https://docs.overturemaps.org/attribution/') 're-capture' @('--allow-shared-host')
C 'S04'  'Sensor.Community' @('https://data.sensor.community/airrohr/v1/filter/box=44.60,20.20,44.95,20.65','https://maps.sensor.community/') @('https://sensor.community/en/') 're-capture' @('--allow-shared-host')
C 'S135' 'gisportal.rs ArcGIS Server' @('https://gisportal.rs/server/rest/services?f=pjson') @() 're-capture' $null
C 'S138' 'UNESCO World Heritage Centre' @('https://whc.unesco.org/en/list/xml/','https://whc.unesco.org/en/statesparties/rs') @() 're-capture' $null
C 'S139' 'ISRBC Sava Commission' @('https://www.savacommission.org/') @() 're-capture' $null
C 'S140' 'ICPDR TNMN water quality database' @('https://wq-db.icpdr.org/') @() 're-capture' $null
C 'S144' 'transit.land feed registry' @('https://www.transit.land/feeds/f-sry-cityofbelgradesecretariatforpublictransport') @() 're-capture through the RFC 9309 engine - urllib said allowed, longest-match says disallowed' $null
C 'S145' 'Beogradski sajam - fair calendar' @('https://www.sajam.rs/en/') @() 're-capture' $null
C 'S13'  'Belgrade static GTFS on data.gov.rs' @('https://data.gov.rs/sr/datasets/gradski-javni-prevoz-u-beogradu-gtfs/') @() 'Serbian Open Data Licence; last updated 2025-10-31, cadence irregular' @('--allow-shared-host')
C 'S141' 'Wikidata Query Service' @('https://query.wikidata.org/sparql') @('https://www.wikidata.org/wiki/Wikidata:Licensing') 're-capture through RFC 9309 engine' @('--needs-decision','robots.txt at query.wikidata.org disallows /sparql for User-agent: *. The evident target is search crawlers following expensive query links, not API clients using an endpoint built to be queried programmatically. Letter and intent diverge - EDGE_CASES.md E-009.')
C 'S142' 'Overpass API' @('https://overpass-api.de/api/status') @('https://www.openstreetmap.org/copyright') 're-capture through RFC 9309 engine' @('--needs-decision','robots.txt at overpass-api.de disallows /api/ for User-agent: *, while publishing a sitemap under that same path. Same shape as Wikidata - EDGE_CASES.md E-009.')
C 'S143' 'Pleiades - gazetteer of the ancient world' @('https://pleiades.stoa.org/') @() 'named opt-out' @('--refused','robots.txt names anthropic-ai, ClaudeBot and Claude-Web with Disallow: / while User-agent: * permits everything, so a collector under any other name reads as allowed - circumvention by choice of name. Also serves an Anubis anti-AI proof-of-work challenge.')
& $py -B tools/build_provenance_index.py
