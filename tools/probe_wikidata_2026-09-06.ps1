$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$H=@{'Accept'='application/sparql-results+json';'User-Agent'='Beops-Research-Probe/1.0 (urban observatory research)'}
function SparqlToFile($q,$file){
  try{
    $b = "query=" + [uri]::EscapeDataString($q)
    $r = Invoke-WebRequest -Uri 'https://query.wikidata.org/sparql' -Method POST -Body $b -ContentType 'application/x-www-form-urlencoded' -Headers $H -UseBasicParsing -TimeoutSec 180
    [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray())
    Write-Output ("OK  {0}  {1} bytes" -f $file, $r.RawContentLength)
  }catch{ Write-Output ("ERR {0}  {1}" -f $file, $_.Exception.Message) }
}
$q1 = @'
SELECT ?item ?itemLabel ?desigLabel ?coord ?inception ?regnum WHERE {
  ?item wdt:P131* wd:Q3711 ; wdt:P1435 ?desig ; wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P3963 ?regnum }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,sh,en". }
}
'@
SparqlToFile $q1 'wd_belgrade_heritage.json'
$q2 = @'
SELECT ?item ?itemLabel ?coord ?start ?end WHERE {
  VALUES ?item { wd:Q1145407 }
  OPTIONAL { ?item wdt:P625 ?coord } OPTIONAL { ?item wdt:P571 ?start } OPTIONAL { ?item wdt:P576 ?end }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,sr". }
}
'@
SparqlToFile $q2 'wd_singidunum.json'
$q3 = @'
SELECT ?item ?itemLabel ?typeLabel ?coord ?opened WHERE {
  ?item wdt:P31/wdt:P279* wd:Q12280 ; wdt:P131* wd:Q3711 ; wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P31 ?type } OPTIONAL { ?item wdt:P1619 ?opened }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,en". }
}
'@
SparqlToFile $q3 'wd_belgrade_bridges.json'
$q4 = @'
SELECT ?item ?itemLabel ?capacity ?coord ?opened WHERE {
  ?item wdt:P31/wdt:P279* wd:Q483110 ; wdt:P131* wd:Q3711 ; wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P1083 ?capacity } OPTIONAL { ?item wdt:P1619 ?opened }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,en". }
}
'@
SparqlToFile $q4 'wd_belgrade_stadiums.json'
$q5 = @'
SELECT ?item ?itemLabel ?coord ?inception ?heritageLabel WHERE {
  ?item wdt:P131* wd:Q3711 ; wdt:P625 ?coord ;
        wdt:P31/wdt:P279* wd:Q839954 .
  OPTIONAL { ?item wdt:P1435 ?heritage } OPTIONAL { ?item wdt:P571 ?inception }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sr,en". }
}
'@
SparqlToFile $q5 'wd_belgrade_archaeology.json'
