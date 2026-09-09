$ErrorActionPreference='Continue'
$h='www.parking-servis.co.rs'
try{ $r=Invoke-WebRequest -Uri ("https://"+$h+"/lat/garaze-i-parkiralista") -UseBasicParsing -TimeoutSec 30
     Write-Output ("PS-OK  http "+$r.StatusCode+"  (Windows trust store accepts it)") }
catch{ Write-Output ("PS-ERR "+$_.Exception.Message) }
try{
  $t=New-Object Net.Sockets.TcpClient($h,443)
  $ss=New-Object Net.Security.SslStream($t.GetStream(),$false,({param($a,$b,$c,$d) $true}))
  $ss.AuthenticateAsClient($h)
  $c=New-Object Security.Cryptography.X509Certificates.X509Certificate2($ss.RemoteCertificate)
  Write-Output ("SUBJECT  "+$c.Subject)
  Write-Output ("ISSUER   "+$c.Issuer)
  Write-Output ("VALID    "+$c.NotBefore+"  ..  "+$c.NotAfter)
  Write-Output ("THUMB    "+$c.Thumbprint)
  $ch=New-Object Security.Cryptography.X509Certificates.X509Chain
  $ok=$ch.Build($c)
  Write-Output ("CHAIN-OK "+$ok+"   elements sent/built = "+$ch.ChainElements.Count)
  foreach($s in $ch.ChainStatus){ Write-Output ("  STATUS "+$s.Status+" :: "+$s.StatusInformation) }
  foreach($e in $ch.ChainElements){ Write-Output ("  ELEM   "+$e.Certificate.Subject) }
  $ss.Close(); $t.Close()
}catch{ Write-Output ("TLS-ERR "+$_.Exception.Message) }
Write-Output "--- what python/certifi says ---"
& C:\Svemir\python.cmd -c "import ssl,socket,certifi;ctx=ssl.create_default_context(cafile=certifi.where());
try:
    s=ctx.wrap_socket(socket.create_connection(('www.parking-servis.co.rs',443),10),server_hostname='www.parking-servis.co.rs');print('PY-OK', s.version());s.close()
except Exception as e: print('PY-ERR', type(e).__name__, e)"
