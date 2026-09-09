$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=700){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,application/ld+json,*/*'} -UseBasicParsing -TimeoutSec 45
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    Write-Output ("OK  {0}  {1}B" -f $u,$r.RawContentLength)
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output ("    "+($c -replace "`r?`n"," "))
  }catch{ $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("--  {0}  [{1}]" -f $u,$s) }
}
Write-Output "@@@ H7a national DCAT catalogue"
G 'https://data.gov.rs/api/1/site/catalog.jsonld' $null 400
G 'https://data.gov.rs/catalog.jsonld' $null 400
G 'https://data.gov.rs/data.json' $null 400
G 'https://data.gov.rs/api/1/organizations/?page_size=1' $null 500
Write-Output "@@@ H7b meteorological HVD - RHMZ"
G 'https://opendata.hidmet.gov.rs/' $null 300
G 'http://opendata.hidmet.gov.rs/api/v1/metadata' $null 400
G 'https://www.hidmet.gov.rs/data.json' $null 300
G 'https://data.gov.rs/api/1/organizations/?q=hidro' $null 500
Write-Output "@@@ H7c mobility HVD"
G 'https://data.gov.rs/api/1/datasets/?q=GTFS&page_size=5' $null 600
G 'https://data.gov.rs/api/1/organizations/?q=saobracaj' $null 500
Write-Output "@@@ H1 heritage with geometry"
G 'https://opendata.geosrbija.rs/nepokretnakulturnadobra' 'kd_all.json' 900
G 'https://opendata.geosrbija.rs/ustanovekulture' 'ustanove.json' 500
Write-Output "@@@ H3 schools with locations"
G 'https://opendata.mpn.gov.rs/srv/Vs/PodaciOLOPJSON' 'skole_lokacije.json' 800
Write-Output "@@@ H4 pollen API"
G 'http://77.46.150.200/api/opendata/locations/' 'polen_locations.json' 700
Write-Output "@@@ H2 EMF drive test"
G 'https://emf.ratel.rs/drive-test-open-data/open-data-7-1.json' 'emf_7_1.json' 700
