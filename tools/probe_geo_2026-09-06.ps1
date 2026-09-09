$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=1200){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,*/*'} -UseBasicParsing -TimeoutSec 90
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    Write-Output ("### {0}  HTTP {1}  {2} bytes" -f $u,$r.StatusCode,$r.RawContentLength)
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output $c
  }catch{
    $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("### {0}  ERR {1} :: {2}" -f $u,$s,$_.Exception.Message)
  }
  Write-Output ""
}
Write-Output "@@@ A. opendata.geosrbija.rs - find the catalogue of categories and layers"
G 'https://opendata.geosrbija.rs/' 'geosrbija_index.html' 200
try{
  $h=[System.Text.Encoding]::UTF8.GetString([System.IO.File]::ReadAllBytes((Join-Path $out 'geosrbija_index.html')))
  $m=[regex]::Matches($h,'category=([A-Za-z0-9_\-]+)&layer=([A-Za-z0-9_\-]+)')
  $s=@{}; foreach($x in $m){ $s[$x.Value]=1 }
  Write-Output ("category/layer pairs found in the page: {0}" -f $s.Count)
  $s.Keys | Sort-Object | ForEach-Object { Write-Output ("   "+$_) }
  $sc=[regex]::Matches($h,'src="([^"]+\.js[^"]*)"'); foreach($x in $sc){ Write-Output ("   script: "+$x.Groups[1].Value) }
}catch{ Write-Output ("parse err "+$_.Exception.Message) }

Write-Output "@@@ B. Mining ArcGIS - count polygons intersecting the Belgrade bbox"
foreach($lyr in 49,50,51){
  $u = "http://gis.mre.gov.rs/arcgis/rest/services/OpenData/CISGIR/MapServer/$lyr/query?where=1%3D1&geometry=2247000%2C5560000%2C2300000%2C5620000&geometryType=esriGeometryEnvelope&inSR=102100&spatialRel=esriSpatialRelIntersects&returnCountOnly=true&f=pjson"
  G $u $null 300
}
G 'http://gis.mre.gov.rs/arcgis/rest/services/OpenData/CISGIR/MapServer/50?f=pjson' 'mre_50.json' 700

Write-Output "@@@ C. SEPA hourly air quality - the real endpoint"
G 'https://data.gov.rs/api/1/datasets/?q=%D1%81%D0%B0%D1%82%D0%BD%D0%B5%20%D0%B2%D1%80%D0%B5%D0%B4%D0%BD%D0%BE%D1%81%D1%82%D0%B8&page_size=5' 'dgrs_hourly.json' 1500

Write-Output "@@@ D. Pollen station locations"
G 'https://data.gov.rs/s/resources/alergeni-polen/20250210-182653/polen-lokacije.xlsx' 'polen_lokacije.xlsx' 120
