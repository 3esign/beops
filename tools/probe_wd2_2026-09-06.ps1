$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$H=@{'Accept'='application/sparql-results+json';'User-Agent'='Beops-Research-Probe/1.0 (urban observatory research)'}
function S($q,$file){
  try{
    $r=Invoke-WebRequest -Uri 'https://query.wikidata.org/sparql' -Method POST -Body ("query="+[uri]::EscapeDataString($q)) -ContentType 'application/x-www-form-urlencoded' -Headers $H -UseBasicParsing -TimeoutSec 180
    [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray())
    Write-Output ("OK  {0}  {1} bytes" -f $file,$r.RawContentLength)
  }catch{ Write-Output ("ERR {0}  {1}" -f $file,$_.Exception.Message) }
}
S @'
SELECT ?item ?itemLabel ?coord ?opened ?length WHERE {
  ?item wdt:P31/wdt:P279* wd:Q12280 ; wdt:P131 wd:Q3711 ; wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P1619 ?opened } OPTIONAL { ?item wdt:P2043 ?length }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,en". }
}
'@ 'wd_belgrade_bridges.json'
S @'
SELECT ?item ?itemLabel ?coord ?start ?end ?typeLabel WHERE {
  ?item rdfs:label "Singidunum"@en ; wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P571 ?start } OPTIONAL { ?item wdt:P576 ?end } OPTIONAL { ?item wdt:P31 ?type }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,sr". }
}
'@ 'wd_singidunum2.json'
S @'
SELECT ?item ?itemLabel ?typeLabel ?coord ?inception WHERE {
  ?item wdt:P131* wd:Q3711 ; wdt:P625 ?coord ; wdt:P31 ?type .
  VALUES ?type { wd:Q33506 wd:Q41176 wd:Q483110 wd:Q1060829 wd:Q11707 wd:Q17350442 wd:Q57660343 }
  OPTIONAL { ?item wdt:P571 ?inception }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,en". }
} LIMIT 4000
'@ 'wd_belgrade_venues.json'
S @'
SELECT ?item ?itemLabel ?coord ?inception ?heritageLabel WHERE {
  ?item wdt:P131* wd:Q3711 ; wdt:P625 ?coord ; wdt:P31/wdt:P279* wd:Q839954 .
  OPTIONAL { ?item wdt:P1435 ?heritage } OPTIONAL { ?item wdt:P571 ?inception }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,en". }
} LIMIT 2000
'@ 'wd_belgrade_archaeology.json'
