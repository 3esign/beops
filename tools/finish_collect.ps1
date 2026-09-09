Set-Location 'D:\Svemir\!Projekti\Beops'
$py='C:\Svemir\python.cmd'
& $py -B tools/legal_capture.py --sid S06 --name 'SEPA verified daily air quality archive' --url 'https://data.gov.rs/sr/datasets/kvalitet-vazdukha/' --note 'verified daily, 2011-2024 xlsx' --allow-shared-host 2>&1 | Select-String 'allowed_for_us|capture_ok'
& $py -B tools/build_provenance_index.py
& $py -B research/collect_permitted.py --plan research/COLLECTION_PLAN.json --only S06,S149,S155,S159
