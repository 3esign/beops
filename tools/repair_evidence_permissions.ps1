# Repair only the four verified Beops evidence packets. Never changes payload bytes.
# An elevated launch may be needed to read the old creator-only ACLs.
param(
  [ValidateSet('Audit','Apply','Rollback')][string]$Mode='Audit',
  [string]$ProjectRoot=(Join-Path $PSScriptRoot '..'),
  [string]$JournalPath
)
$ErrorActionPreference='Stop'
# A PowerShell 7 parent may export its incompatible module directory to PS 5.1.
# Use this process's own standard modules; never change the machine setting.
$env:PSModulePath=Join-Path $PSHOME 'Modules'
. (Join-Path $PSScriptRoot 'publish_safety.ps1')
$root=Get-BeopsFullPath $ProjectRoot
$trail=Join-Path $root 'research/_trail'
$names=@('ai-quality-20260912','ai-quality-20260913','execution-baseline-20260912T212944Z','execution-baseline-20260912T213239Z')
$proofPath=Join-Path $trail 'remediation-20260914/r01-recovery.json'
$proof=Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if ($proof.schema -ne 'beops-evidence-recovery/v1' -or @($proof.files).Count -ne 30) { throw 'Expected the original 30-file recovery manifest' }
$expected=@{}
foreach ($file in $proof.files) {
  $parts=$file.path.Split('/')
  if ($parts.Count -ne 4 -or $parts[0] -ne 'research' -or $parts[1] -ne '_trail' -or $parts[2] -notin $names -or $parts[3] -notmatch '^[a-zA-Z0-9_.-]+$' -or $parts[3] -in @('.','..') -or $file.sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Unsafe evidence manifest path or digest' }
  $path=Join-Path $root $file.path
  if ($expected.ContainsKey($path)) { throw 'Duplicate evidence path' }
  $expected[$path]=$file
}
function Assert-ExactTarget([string]$Path) {
  $full=[IO.Path]::GetFullPath($Path)
  $allowed=($full -in @($names | ForEach-Object { Join-Path $trail $_ })) -or $expected.ContainsKey($full)
  if (-not $allowed -or -not $full.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside fixed evidence scope' }
  $item=Get-Item -LiteralPath $full -Force -ErrorAction Stop
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point refused' }
  if ((Get-BeopsFullPath $full) -ne $full) { throw 'Physical path mismatch' }
  return $full
}
function Write-Journal($Record,[string]$Path) {
  $text=$Record | ConvertTo-Json -Depth 12
  [IO.File]::WriteAllText($Path,$text,(New-Object Text.UTF8Encoding($false)))
}
function Set-AccessOnly([string]$Path,[string]$Sddl,[bool]$EnableInheritance) {
  # Set-Acl can request SACL privileges when given the whole Get-Acl object.
  # Construct and persist only the DACL; ownership and audit policy stay intact.
  $directory=[IO.Directory]::Exists($Path)
  $security=if ($directory) { New-Object Security.AccessControl.DirectorySecurity } else { New-Object Security.AccessControl.FileSecurity }
  $security.SetSecurityDescriptorSddlForm($Sddl,[Security.AccessControl.AccessControlSections]::Access)
  if ($EnableInheritance) { $security.SetAccessRuleProtection($false,$true) }
  if ($directory) { [IO.Directory]::SetAccessControl($Path,$security) } else { [IO.File]::SetAccessControl($Path,$security) }
}
if ($Mode -eq 'Rollback') {
  if (-not $JournalPath) { throw 'Rollback requires its saved journal' }
  $journal=Get-Content -LiteralPath $JournalPath -Raw | ConvertFrom-Json
  if ($journal.schema -ne 'beops-evidence-acl-repair/v1' -or $journal.root -ne $root -or @($journal.before).Count -ne 34) { throw 'Journal scope mismatch' }
  $seen=@{}
  foreach ($entry in $journal.before) { $null=Assert-ExactTarget $entry.path; if ($seen.ContainsKey($entry.path)) { throw 'Duplicate rollback path' }; $seen[$entry.path]=$true }
  foreach ($entry in @($journal.before | Sort-Object { $_.path.Length } -Descending)) {
    Set-AccessOnly $entry.path $entry.sddl $false
  }
  Write-Output '{"state":"rolled_back","payloads_modified":false}'
  exit 0
}
$before=@()
foreach ($name in $names) {
  $directory=Assert-ExactTarget (Join-Path $trail $name)
  $acl=Get-Acl -LiteralPath $directory
  $ownerSid=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
  $rules=@($acl.GetAccessRules($true,$false,[Security.Principal.SecurityIdentifier]))
  if ($acl.AreAccessRulesProtected) {
    $allowedSids=@('S-1-3-4','S-1-5-18','S-1-5-32-544',$ownerSid)
    if ($rules.Count -lt 2 -or @($rules | Where-Object { $_.IdentityReference.Value -notin $allowedSids -or $_.AccessControlType -ne 'Allow' }).Count -gt 0) { throw "Unrecognized protected ACL; no automatic repair: $name" }
  }
  $before+=@{path=$directory;owner=$acl.Owner;owner_sid=$ownerSid;sddl=$acl.Sddl;protected=$acl.AreAccessRulesProtected;kind='directory'}
  $children=@(Get-ChildItem -LiteralPath $directory -Force)
  $wanted=@($expected.Keys | Where-Object { (Split-Path -Parent $_) -eq $directory })
  if ($children.Count -ne $wanted.Count) { throw "Unexpected file inventory: $name" }
  foreach ($child in $children) {
    $path=Assert-ExactTarget $child.FullName
    if ($child.PSIsContainer -or -not $expected.ContainsKey($path)) { throw 'Unexpected child' }
    $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $expected[$path].sha256 -or $child.Length -ne $expected[$path].bytes) { throw "Payload differs from verified Git recovery: $path" }
    $a=Get-Acl -LiteralPath $path
    if (@($a.Access | Where-Object AccessControlType -eq 'Deny').Count -gt 0) { throw 'Explicit deny requires separate review' }
    $before+=@{path=$path;owner=$a.Owner;sddl=$a.Sddl;protected=$a.AreAccessRulesProtected;kind='file';sha256=$hash;bytes=$child.Length}
  }
}
if ($before.Count -ne 34) { throw 'Incomplete ACL backup' }
$outDir=Join-Path $trail 'permissions-20260914'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$output=Join-Path $outDir ('acl-'+$Mode.ToLowerInvariant()+'-'+[guid]::NewGuid().ToString('N')+'.json')
$record=[ordered]@{schema='beops-evidence-acl-repair/v1';at=[DateTimeOffset]::UtcNow.ToString('o');root=$root;mode=$Mode;identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;state='verified_before_change';before=$before;applied=@();after=@();payloads_modified=$false;error=$null}
Write-Journal $record $output
if ($Mode -eq 'Audit') { Write-Output (@{state='audited';journal=$output;files=30;protected_directories=@($before | Where-Object { $_.kind -eq 'directory' -and $_.protected }).Count} | ConvertTo-Json -Compress); exit 0 }
try {
  foreach ($entry in $before) {
    $a=Get-Acl -LiteralPath $entry.path
    if ($a.AreAccessRulesProtected) {
      Set-AccessOnly $entry.path $a.Sddl $true
      $record.applied+=@($entry.path)
      Write-Journal $record $output
    }
  }
  foreach ($entry in $before) {
    $a=Get-Acl -LiteralPath $entry.path
    if ($a.AreAccessRulesProtected) { throw 'Inheritance remains blocked' }
    if (@($a.Access | Where-Object IsInherited).Count -eq 0) { throw 'No inherited project rules after repair' }
    if ($entry.kind -eq 'file' -and (Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Payload changed during ACL repair' }
    $record.after+=@(@{path=$entry.path;owner=$a.Owner;sddl=$a.Sddl;protected=$a.AreAccessRulesProtected})
  }
  $record.state='repaired_and_hash_verified'
} catch { $record.state='failed';$record.error=$_.Exception.Message;Write-Journal $record $output;throw }
Write-Journal $record $output
Write-Output (@{state=$record.state;journal=$output;changed=$record.applied.Count;files_verified=30;payloads_modified=$false} | ConvertTo-Json -Compress)
