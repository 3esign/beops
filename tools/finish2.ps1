Set-Location 'D:\Svemir\!Projekti\Beops'
& C:\Svemir\python.cmd -B research/collect_permitted.py --plan research/COLLECTION_PLAN.json --only S06,S155 2>&1 | Select-Object -Last 8
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
cmd /c "npm test 2>&1" | Select-String "Ran |^OK|FAILED"
git add -A
git -c user.name="Svemir" -c user.email="svemir@local" commit -q -F tools/commitmsg7.txt 2>&1 | Select-Object -Last 3
git log --oneline -1
git count-objects -vH | Select-String "size-pack"
