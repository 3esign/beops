$ProgressPreference='SilentlyContinue'
Set-Location 'D:\Svemir\!Projekti\Beops'
function Post($u,$body,$ct,$acc){
  try{ $r=Invoke-WebRequest -Uri $u -Method POST -Body $body -ContentType $ct -Headers @{'Accept'=$acc;'User-Agent'='Beops-Research-Probe/1.0 (urban observatory research)'} -UseBasicParsing -TimeoutSec 120
       return @{ok=$true;code=$r.StatusCode;body=$r.Content} }
  catch{ $c=$null; if($_.Exception.Response){$c=[int]$_.Exception.Response.StatusCode}
         return @{ok=$false;code=$c;body=$_.Exception.Message} }
}
function Get1($u,$acc){
  try{ $r=Invoke-WebRequest -Uri $u -Headers @{'Accept'=$acc;'User-Agent'='Beops-Research-Probe/1.0 (urban observatory research)'} -UseBasicParsing -TimeoutSec 120
       return @{ok=$true;code=$r.StatusCode;body=$r.Content} }
  catch{ $c=$null; if($_.Exception.Response){$c=[int]$_.Exception.Response.StatusCode}
         return @{ok=$false;code=$c;body=$_.Exception.Message} }
}

Write-Output "########## 1. WIKIDATA - cultural heritage monuments in Belgrade with coordinates"
$q = @'
SELECT (COUNT(DISTINCT ?item) AS ?n) WHERE {
  ?item wdt:P131* wd:Q3711 .
  ?item wdt:P1435 ?desig .
  ?item wdt:P625 ?coord .
}
'@
$r = Post 'https://query.wikidata.org/sparql' ("query=" + [uri]::EscapeDataString($q)) 'application/x-www-form-urlencoded' 'application/sparql-results+json'
Write-Output ("wikidata count: ok={0} code={1}" -f $r.ok,$r.code)
Write-Output ($r.body.Substring(0,[Math]::Min(700,$r.body.Length)))

Write-Output "`n########## 1b. WIKIDATA - breakdown by heritage designation"
$q2 = @'
SELECT ?desigLabel (COUNT(DISTINCT ?item) AS ?n) WHERE {
  ?item wdt:P131* wd:Q3711 . ?item wdt:P1435 ?desig . ?item wdt:P625 ?coord .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,sr,sh". }
} GROUP BY ?desigLabel ORDER BY DESC(?n)
'@
$r2 = Post 'https://query.wikidata.org/sparql' ("query=" + [uri]::EscapeDataString($q2)) 'application/x-www-form-urlencoded' 'application/sparql-results+json'
Write-Output ("ok={0} code={1}" -f $r2.ok,$r2.code)
Write-Output ($r2.body.Substring(0,[Math]::Min(2200,$r2.body.Length)))

Write-Output "`n########## 2. OVERPASS - bridges in the Belgrade bbox"
$oq = '[out:json][timeout:90];(way["bridge"](44.6,20.2,44.95,20.65);relation["bridge"](44.6,20.2,44.95,20.65););out count;'
$r3 = Post 'https://overpass-api.de/api/interpreter' ("data=" + [uri]::EscapeDataString($oq)) 'application/x-www-form-urlencoded' 'application/json'
Write-Output ("overpass bridges: ok={0} code={1}" -f $r3.ok,$r3.code)
Write-Output ($r3.body.Substring(0,[Math]::Min(900,$r3.body.Length)))

Write-Output "`n########## 2b. OVERPASS - named bridges over the Sava and Danube"
$oq2 = '[out:json][timeout:90];way["bridge"]["name"]["highway"~"motorway|trunk|primary|secondary"](44.75,20.3,44.92,20.55);out tags;'
$r4 = Post 'https://overpass-api.de/api/interpreter' ("data=" + [uri]::EscapeDataString($oq2)) 'application/x-www-form-urlencoded' 'application/json'
Write-Output ("ok={0} code={1} len={2}" -f $r4.ok,$r4.code,$r4.body.Length)
if($r4.ok){ $j=$r4.body | ConvertFrom-Json; ($j.elements | ForEach-Object { $_.tags.name } | Sort-Object -Unique) -join ' | ' }

Write-Output "`n########## 3. SENSOR.COMMUNITY - live nodes in the Belgrade bbox"
$r5 = Get1 'https://data.sensor.community/airrohr/v1/filter/box=44.60,20.20,44.95,20.65' 'application/json'
Write-Output ("ok={0} code={1} len={2}" -f $r5.ok,$r5.code,$r5.body.Length)
if($r5.ok){ $j=$r5.body | ConvertFrom-Json
  Write-Output ("readings: {0}" -f $j.Count)
  Write-Output ("distinct sensor ids: {0}" -f (($j | ForEach-Object { $_.sensor.id } | Sort-Object -Unique).Count))
  Write-Output ("distinct locations: {0}" -f (($j | ForEach-Object { $_.location.id } | Sort-Object -Unique).Count))
  Write-Output ("value types: {0}" -f ((($j | ForEach-Object { $_.sensordatavalues } | ForEach-Object { $_.value_type }) | Sort-Object -Unique) -join ', '))
}

Write-Output "`n########## 4. PLEIADES robots.txt (checking before touching anything)"
$r6 = Get1 'https://pleiades.stoa.org/robots.txt' 'text/plain'
Write-Output ("ok={0} code={1}" -f $r6.ok,$r6.code)
Write-Output ($r6.body.Substring(0,[Math]::Min(1200,$r6.body.Length)))
