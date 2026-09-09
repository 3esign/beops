$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$UA='Beops-Research-Probe/1.0 (urban observatory research)'
function G($u,$file,$show=600){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,text/xml,*/*'} -UseBasicParsing -TimeoutSec 45
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=$r.Content; if($c -is [byte[]]){ $c=[System.Text.Encoding]::UTF8.GetString($c) }
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output ("### {0}  HTTP {1}  {2} bytes" -f $u,$r.StatusCode,$r.RawContentLength)
    Write-Output $c
  }catch{
    $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("### {0}  ERR {1}  {2}" -f $u,$s,$_.Exception.Message)
  }
  Write-Output ""
}
Write-Output "@@@@@@@@@@ A. GEOSRBIJA / national spatial data infrastructure"
G 'https://a3.geosrbija.rs/rest/services?f=pjson' $null 900
G 'https://geosrbija.rs/robots.txt' $null 400
G 'https://opendata.geosrbija.rs/' $null 500

Write-Output "@@@@@@@@@@ B. data.gov.rs API - how many datasets, and how many mention Beograd"
G 'https://data.gov.rs/api/1/datasets/?page_size=1&q=beograd' 'dgrs_beograd.json' 700
G 'https://data.gov.rs/api/1/site/' $null 700
G 'https://data.gov.rs/robots.txt' $null 400

Write-Output "@@@@@@@@@@ C. RGZ - Republicki geodetski zavod, address register / cadastre"
G 'https://www.rgz.gov.rs/robots.txt' $null 300
G 'https://ossa.rgz.gov.rs/' $null 400

Write-Output "@@@@@@@@@@ D. Statistical Office of Serbia - dissemination database API"
G 'https://data.stat.gov.rs/robots.txt' $null 300
G 'https://www.stat.gov.rs/robots.txt' $null 300

Write-Output "@@@@@@@@@@ E. City of Belgrade - is there a city open data portal"
G 'https://data.beograd.rs/' $null 400
G 'https://www.beograd.rs/robots.txt' $null 400
