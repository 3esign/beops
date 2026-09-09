$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\probe'
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
function G($u,$file,$show=500){
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
Write-Output "@@@ World Bank Projects API"
G 'https://search.worldbank.org/api/v3/projects?format=json&countrycode_exact=RS&rows=3' 'wb_rs.json' 700
G 'https://search.worldbank.org/api/v2/projects?format=json&countrycode_exact=RS&rows=2' $null 400
Write-Output "@@@ IATI Registry (CKAN, keyless)"
G 'https://iatiregistry.org/api/3/action/package_search?q=Serbia&rows=3' 'iati_rs.json' 600
Write-Output "@@@ CORDIS bulk"
G 'https://cordis.europa.eu/data/cordis-HORIZONprojects-json.zip' $null 120
G 'https://cordis.europa.eu/datalab/api/' $null 300
Write-Output "@@@ EIB"
G 'https://www.eib.org/robots.txt' $null 300
G 'https://www.eib.org/en/projects/loans/index.htm?q=&sortColumn=loanParts.signatureDate&sortDir=desc&pageNumber=0&itemPerPage=10&pageable=true&language=EN&defaultLanguage=EN&loanPartYearFrom=2015&loanPartYearTo=2026&orCountries.region=&orCountries.country=RS' $null 300
Write-Output "@@@ EBRD"
G 'https://www.ebrd.com/robots.txt' $null 300
Write-Output "@@@ WBIF"
G 'https://www.wbif.eu/robots.txt' $null 300
G 'https://www.wbif.eu/beneficiaries/serbia' $null 300
Write-Output "@@@ keep.eu (Interreg projects)"
G 'https://keep.eu/robots.txt' $null 300
Write-Output "@@@ AidData"
G 'https://www.aiddata.org/robots.txt' $null 300
Write-Output "@@@ EU Financial Transparency System"
G 'https://ec.europa.eu/budget/financial-transparency-system/robots.txt' $null 300
