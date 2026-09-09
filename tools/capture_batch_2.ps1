Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
function Cap($sid,$name,$urls,$terms,$note,$extra){
  $a=@('-B','tools/legal_capture.py','--sid',$sid,'--name',$name)
  foreach($u in $urls){ $a+=@('--url',$u) }; foreach($t in $terms){ $a+=@('--terms',$t) }
  $a+=@('--note',$note); if($extra){ $a+=$extra }
  Write-Output ("===== "+$sid); & $py @a 2>&1 | Select-String -Pattern 'allowed_for_us|capture_ok|regime|opt_out_signals_seen|REFUSED|\*' | Select-Object -First 12
}
Cap 'S141' 'Wikidata Query Service' @('https://query.wikidata.org/sparql') @('https://www.wikidata.org/wiki/Wikidata:Licensing') 'keyless SPARQL, CC0' $null
Cap 'S142' 'Overpass API' @('https://overpass-api.de/api/status') @('https://www.openstreetmap.org/copyright') 'keyless, ODbL, response carries timestamp_osm_base' $null
Cap 'S143' 'Pleiades - gazetteer of the ancient world' @('https://pleiades.stoa.org/') @() 'NAMED OPT-OUT: robots.txt disallows anthropic-ai, ClaudeBot, Claude-Web' $null
Cap 'S144' 'transit.land feed registry' @('https://www.transit.land/feeds/f-sry-cityofbelgradesecretariatforpublictransport') @() 'robots.txt disallows /feeds/' $null
Cap 'S145' 'Beogradski sajam - fair calendar' @('https://www.sajam.rs/en/') @('https://www.sajam.rs/en/terms-of-use/') 'nothing collected yet' $null
C:\Svemir\python.cmd -B tools/build_provenance_index.py
