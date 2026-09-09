$ErrorActionPreference = 'Stop'
$url = 'https://www.parking-servis.co.rs/lat/garaze-i-parkiralista'
$request = [System.Net.HttpWebRequest]::Create($url)
$request.Method = 'GET'
$request.UserAgent = 'Beops-Research/0.2 (bounded public source audit)'
$request.AllowAutoRedirect = $false
$request.Timeout = 15000
$request.ReadWriteTimeout = 15000
$response = $null
$stream = $null
$memory = New-Object System.IO.MemoryStream
$watch = [System.Diagnostics.Stopwatch]::StartNew()
try {
    # Use Windows certificate validation unchanged; never suppress TLS failures.
    $response = $request.GetResponse()
    if ([int]$response.StatusCode -ne 200) { throw 'Expected HTTP 200' }
    $stream = $response.GetResponseStream()
    $buffer = New-Object byte[] 8192
    while (($n = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        if ($memory.Length + $n -gt 3000000) { throw 'Response exceeds byte limit' }
        if ($watch.Elapsed.TotalSeconds -gt 25) { throw 'Response exceeds time budget' }
        $memory.Write($buffer, 0, $n)
    }
    [ordered]@{
        url = $url
        status = [int]$response.StatusCode
        content_type = $response.ContentType
        http_date = $response.Headers['Date']
        last_modified = $response.Headers['Last-Modified']
        retrieved_at = [DateTime]::UtcNow.ToString('o')
        elapsed_ms = $watch.ElapsedMilliseconds
        transport = 'Windows HttpWebRequest; default certificate verification'
        body_base64 = [Convert]::ToBase64String($memory.ToArray())
    } | ConvertTo-Json -Compress
} catch {
    $status = $null
    $exception = $_.Exception
    while ($null -ne $exception) {
        if ($exception -is [System.Net.WebException] -and $null -ne $exception.Response) {
            $status = [int]$exception.Response.StatusCode
            $exception.Response.Dispose()
            break
        }
        $exception = $exception.InnerException
    }
    [ordered]@{
        url = $url
        status = $status
        error = 'Verified-TLS public request failed'
        attempted_at = [DateTime]::UtcNow.ToString('o')
    } | ConvertTo-Json -Compress
} finally {
    if ($null -ne $stream) { $stream.Dispose() }
    if ($null -ne $response) { $response.Dispose() }
    $memory.Dispose()
}
