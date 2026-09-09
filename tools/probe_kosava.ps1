$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=1000){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,*/*'} -UseBasicParsing -TimeoutSec 90
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    Write-Output ("### {0}  HTTP {1}  {2} bytes" -f $u,$r.StatusCode,$r.RawContentLength)
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output $c
  }catch{ $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("### {0}  ERR {1} :: {2}" -f $u,$s,$_.Exception.Message) }
  Write-Output ""
}
G 'http://opendata.kosava.cloud/api/v1/metadata' 'kosava_metadata.json' 2200
G 'http://opendata.kosava.cloud/api/v1/stations' 'kosava_stations.json' 900
G 'http://opendata.kosava.cloud/api/v1/parameters' 'kosava_parameters.json' 800
G 'http://opendata.kosava.cloud/robots.txt' $null 300
Write-Output "@@@ address register: how big is the national house-number layer?"
try{
  $r=Invoke-WebRequest -Uri 'https://download.geosrbija.rs/download-api/opendata-proxy/export?category=ar&layer=kucni_broj_ar&geometry=true&fileName=kucni_br_gpkg&format=gpkg' -Method Head -Headers @{'User-Agent'=$UA} -UseBasicParsing -TimeoutSec 90
  Write-Output ("HEAD ok {0}  len={1}  type={2}" -f $r.StatusCode,$r.Headers['Content-Length'],$r.Headers['Content-Type'])
}catch{ Write-Output ("HEAD err :: "+$_.Exception.Message) }
Write-Output "@@@ do other geosrbija opendata categories exist?"
foreach($cat in @('ar','kn','rpj','dof','dmr','ppj','sk')){
  try{
    $u="https://download.geosrbija.rs/download-api/opendata-proxy/export?category=$cat&layer=probe&geometry=true&fileName=x&format=csv"
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA} -UseBasicParsing -TimeoutSec 30
    Write-Output ("  {0} -> HTTP {1} {2} bytes" -f $cat,$r.StatusCode,$r.RawContentLength)
  }catch{ $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("  {0} -> {1} {2}" -f $cat,$s,($_.Exception.Message -replace '\s+',' ').Substring(0,[Math]::Min(90,$_.Exception.Message.Length))) }
}
