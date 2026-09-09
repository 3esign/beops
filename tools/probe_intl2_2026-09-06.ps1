$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=600){
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json,*/*'} -UseBasicParsing -TimeoutSec 60
    if($file){ [System.IO.File]::WriteAllBytes((Join-Path $out $file), $r.RawContentStream.ToArray()) }
    $c=[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    Write-Output ("OK   {0}   {1}B" -f $u,$r.RawContentLength)
    if($c.Length -gt $show){$c=$c.Substring(0,$show)}
    Write-Output ("     "+($c -replace "`r?`n"," "))
  }catch{ $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("--   {0}   [{1}]" -f $u,$s) }
  Write-Output ""
}
Write-Output "@@@ World Bank: does it expose geolocation, and all 108 Serbia projects"
G 'https://search.worldbank.org/api/v3/projects?format=json&countrycode_exact=RS&rows=200&fl=id,project_name,boardapprovaldate,closingdate,totalamt,impagency,sector1,geoLocID,geoLocName,latitude,longitude,status' 'wb_rs_all.json' 700
Write-Output "@@@ IATI registry - correct CKAN call"
G 'https://iatiregistry.org/api/3/action/package_list' $null 300
G 'https://iatiregistry.org/api/action/package_search?q=Serbia' $null 300
Write-Output "@@@ keep.eu - is there an API"
G 'https://keep.eu/wp-json/' $null 400
Write-Output "@@@ ec.europa.eu robots"
G 'https://ec.europa.eu/robots.txt' $null 500
Write-Output "@@@ EBRD project list"
G 'https://www.ebrd.com/home/work-with-us/project-finance/project-summary-documents.html?1=1&filterCountry=Serbia' $null 250
Write-Output "@@@ CORDIS - is there a smaller organisations file"
G 'https://cordis.europa.eu/data/' $null 400
