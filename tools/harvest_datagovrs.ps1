$ProgressPreference='SilentlyContinue'
$out='D:\Svemir\!Projekti\Beops\research\_scratch\datagovrs'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$UA='Beops-Research-Probe/1.0 (urban observatory research; identifies honestly)'
$page=1; $total=$null; $n=0
while($true){
  $u = "https://data.gov.rs/api/1/datasets/?page_size=100&page=$page"
  try{
    $r=Invoke-WebRequest -Uri $u -Headers @{'User-Agent'=$UA;'Accept'='application/json'} -UseBasicParsing -TimeoutSec 90
    [System.IO.File]::WriteAllBytes((Join-Path $out ("page_{0:D3}.json" -f $page)), $r.RawContentStream.ToArray())
    $j = [System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json
    if($null -eq $total){ $total = $j.total; Write-Output ("total datasets: {0}" -f $total) }
    $n += $j.data.Count
    if($page % 5 -eq 0){ Write-Output ("  page {0}  cumulative {1}" -f $page,$n) }
    if($j.data.Count -eq 0 -or $n -ge $total){ break }
    $page++
    Start-Sleep -Milliseconds 700
  }catch{
    $s=$null; if($_.Exception.Response){$s=[int]$_.Exception.Response.StatusCode}
    Write-Output ("ERR page {0} status {1} :: {2}" -f $page,$s,$_.Exception.Message); break
  }
  if($page -gt 45){ Write-Output "page cap reached"; break }
}
Write-Output ("harvested {0} datasets across {1} pages" -f $n,$page)
