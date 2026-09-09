$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\newtech'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($tag,$u,$file,$show=320){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,*/*'} -UseBasicParsing -TimeoutSec 40
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output ("OK  [{0}] {1}B  {2}" -f $tag,$r.RawContentLength,$u)
    Write-Output ("    "+($c -replace "`r?`n"," "))
  }catch{ $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("--  [{0}] {1}  {2}" -f $tag,$s,$u) }
}
# BBOX Belgrade: 20.20,44.60 .. 20.65,44.95
Write-Output "########## LIFE - the city as a habitat"
G 'GBIF'      'https://api.gbif.org/v1/occurrence/search?decimalLatitude=44.60,44.95&decimalLongitude=20.20,20.65&limit=1' 'gbif.json' 420
G 'GBIF-yr'   'https://api.gbif.org/v1/occurrence/search?decimalLatitude=44.60,44.95&decimalLongitude=20.20,20.65&facet=year&facetLimit=40&limit=0' 'gbif_years.json' 700
G 'iNat'      'https://api.inaturalist.org/v1/observations?nelat=44.95&nelng=20.65&swlat=44.60&swlng=20.20&per_page=1' 'inat.json' 380
G 'xeno-canto' 'https://xeno-canto.org/api/2/recordings?query=cnt:Serbia' 'xc.json' 320
Write-Output "########## SIGHT - street imagery, after the camera refusals"
G 'Panoramax' 'https://api.panoramax.xyz/api/search?bbox=20.20,44.60,20.65,44.95&limit=1' 'panoramax.json' 400
G 'KartaView' 'https://api.openstreetcam.org/2.0/photo/?bbTopLeft=44.95,20.20&bbBottomRight=44.60,20.65&itemsPerPage=1' 'kartaview.json' 340
G 'Mapillary' 'https://graph.mapillary.com/images?bbox=20.20,44.60,20.65,44.95&limit=1' $null 260
Write-Output "########## SKY - open ADS-B without an account"
G 'adsb.lol'  'https://api.adsb.lol/v2/point/44.80/20.45/40' 'adsblol.json' 360
G 'airplanes.live' 'https://api.airplanes.live/v2/point/44.80/20.45/40' $null 300
Write-Output "########## GROUND - citizen seismometers, lightning, radiation"
G 'RSpectrum' 'https://api.raspberryshake.org/v1/stations?network=AM' $null 260
G 'Blitzortung' 'https://www.blitzortung.org/en/robots.txt' $null 200
G 'EURDEP'    'https://remon.jrc.ec.europa.eu/robots.txt' $null 200
Write-Output "########## ENERGY and MOVEMENT"
G 'OpenChargeMap' 'https://api.openchargemap.io/v3/poi?countrycode=RS&maxresults=1&compact=true' $null 300
G 'GBFS-catalog' 'https://raw.githubusercontent.com/MobilityData/gbfs/master/systems.csv' 'gbfs_systems.csv' 200
Write-Output "########## HEAT, LIGHT, BUILT FORM - open satellite products"
G 'GHSL'      'https://human-settlement.emergency.copernicus.eu/robots.txt' $null 200
G 'ECOSTRESS' 'https://cmr.earthdata.nasa.gov/search/collections.json?keyword=ECOSTRESS&page_size=2' 'ecostress.json' 300
G 'S5P-NO2'   'https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel5P/search.json?startDate=2026-09-01T00:00:00Z&maxRecords=1&box=20.20,44.60,20.65,44.95' 'S5P.json' 400
G 'COMET-LiCS' 'https://comet.nerc.ac.uk/comet-lics-portal/robots.txt' $null 200
Write-Output "########## WEATHER from amateurs"
G 'CWOP-MADIS' 'https://api.weather.gov/robots.txt' $null 200
G 'APRS.fi'   'https://aprs.fi/robots.txt' $null 250
Write-Output "########## NOISE by citizens"
G 'NoiseCapture' 'https://noise-planet.org/robots.txt' $null 200
