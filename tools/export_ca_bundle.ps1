# Export the machine's own trusted roots to a PEM, so the capture tool trusts
# exactly what this computer trusts - and so that trust decision is a file we
# can hash and commit rather than an invisible library default.
$out = 'D:\Svemir\!Projekti\Beops\data\ca-bundle-windows.pem'
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
$sb = New-Object System.Text.StringBuilder
$n = 0
foreach ($store in @('Cert:\LocalMachine\Root','Cert:\CurrentUser\Root','Cert:\LocalMachine\CA','Cert:\CurrentUser\CA')) {
  try {
    foreach ($c in Get-ChildItem $store -ErrorAction Stop) {
      $b64 = [Convert]::ToBase64String($c.RawData, 'InsertLineBreaks')
      [void]$sb.AppendLine('# ' + $c.Subject)
      [void]$sb.AppendLine('-----BEGIN CERTIFICATE-----')
      [void]$sb.AppendLine($b64)
      [void]$sb.AppendLine('-----END CERTIFICATE-----')
      $n++
    }
  } catch { }
}
[System.IO.File]::WriteAllText($out, $sb.ToString())
Write-Output ("wrote {0}  certificates={1}  bytes={2}" -f $out, $n, (Get-Item $out).Length)
& C:\Svemir\python.cmd -B -c "import ssl,socket;ctx=ssl.create_default_context(cafile=r'D:\Svemir\!Projekti\Beops\data\ca-bundle-windows.pem');
import sys
for h in ('www.parking-servis.co.rs','registar.ratel.rs','www.putevi-srbije.rs'):
    try:
        s=ctx.wrap_socket(socket.create_connection((h,443),10),server_hostname=h); print('OK ',h,s.version()); s.close()
    except Exception as e: print('ERR',h,type(e).__name__,str(e)[:70])"
