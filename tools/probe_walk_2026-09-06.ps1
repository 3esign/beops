$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=450){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,*/*'} -UseBasicParsing -TimeoutSec 45
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    Write-Output ("OK   {0}   {1}B" -f $u,$r.RawContentLength)
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output ("     "+($c -replace "`r?`n"," "))
  }catch{ $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("--   {0}   [{1}]" -f $u,$s) }
}
Write-Output "@@@ 1. data.europa.eu - the EU portal, Serbia datasets (also the legitimate route to CORDIS)"
G 'https://data.europa.eu/api/hub/search/search?q=Belgrade&limit=3' 'deu_bg.json' 600
G 'https://data.europa.eu/api/hub/search/search?q=Serbia&limit=1' $null 400
G 'https://data.europa.eu/robots.txt' $null 400
Write-Output "@@@ 2. CEOP - unified building permit procedure"
G 'https://ceop.apr.gov.rs/robots.txt' $null 250
G 'https://gradjevinskedozvole.rs/robots.txt' $null 250
G 'https://www.gradjevinskedozvole.rs/' $null 250
Write-Output "@@@ 3. Urbanisticki zavod Beograda and city utilities"
foreach($h in @('https://urbel.com','https://www.urbel.com','https://bvk.rs','https://www.beoelektrane.rs','https://gradskacistoca.rs','https://zelenilo.rs')){ G ($h+'/robots.txt') $null 200 }
Write-Output "@@@ 4. Road Safety Agency database"
G 'https://www.abs.gov.rs/robots.txt' $null 250
G 'https://www.abs.gov.rs/rsl/statistika/baza_podataka' $null 300
Write-Output "@@@ 5. RGZ / geosrbija OGC services"
G 'https://ogc.geosrbija.rs/ows?service=WMS&request=GetCapabilities' $null 400
G 'https://a3.geosrbija.rs/wms?service=WMS&request=GetCapabilities' $null 400
G 'https://geoportal.rgz.gov.rs/robots.txt' $null 250
Write-Output "@@@ 6. Official gazette"
G 'https://www.pravno-informacioni-sistem.rs/robots.txt' $null 300
G 'https://www.slglasnik.com/robots.txt' $null 250
