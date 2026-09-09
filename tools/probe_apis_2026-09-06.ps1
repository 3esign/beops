$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=800){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,*/*'} -UseBasicParsing -TimeoutSec 60
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    Write-Output ("### {0}`n    HTTP {1}  {2} bytes" -f $u,$r.StatusCode,$r.RawContentLength)
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output $c
  }catch{
    $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("### {0}`n    ERR {1} :: {2}" -f $u,$s,$_.Exception.Message)
  }
  Write-Output ""
}
Write-Output "@@@ 1. GEOSRBIJA download API - is there a catalogue of categories/layers?"
G 'https://download.geosrbija.rs/download-api/opendata-proxy/categories' $null 900
G 'https://download.geosrbija.rs/download-api/opendata/categories' $null 900
G 'https://opendata.geosrbija.rs/api/categories' $null 900
G 'https://opendata.geosrbija.rs/robots.txt' $null 300

Write-Output "@@@ 2. Ministry of Mining ArcGIS - is /OpenData/ actually open?"
G 'http://gis.mre.gov.rs/arcgis/rest/services?f=pjson' $null 900
G 'http://gis.mre.gov.rs/arcgis/rest/services/OpenData/CISGIR/MapServer?f=pjson' 'mre_cisgir.json' 1400

Write-Output "@@@ 3. RZS open data REST - tourist overnight stays by municipality"
G 'https://opendata.stat.gov.rs/data/WcfJsonRestService.Service1.svc/dataset/220205IND02/1/json' 'rzs_tourism.json' 700
G 'https://opendata.stat.gov.rs/robots.txt' $null 300

Write-Output "@@@ 4. APR company register open API"
G 'https://openapi.apr.gov.rs/api/opendata/companies' 'apr_companies.json' 600

Write-Output "@@@ 5. SEPA hourly air quality - find the real dataset on data.gov.rs"
G 'https://data.gov.rs/api/1/datasets/?q=%D0%9A%D0%92%D0%90%D0%9B%D0%98%D0%A2%D0%95%D0%A2%20%D0%92%D0%90%D0%97%D0%94%D0%A3%D0%A5%D0%90&page_size=6' 'dgrs_air.json' 1200
