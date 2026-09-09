param(
    [string]$RegistryPath = (Join-Path $PSScriptRoot 'SOURCE_REGISTRY.json'),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '_trail')
)
$ErrorActionPreference = 'Stop'
$registry = Get-Content -LiteralPath $RegistryPath -Raw | ConvertFrom-Json -AsHashtable
$decisionsPath = Join-Path $PSScriptRoot '_trail/PAPER_CODING_DECISIONS_2026-09-06.psv'
$decisions = @(Get-Content -LiteralPath $decisionsPath | ConvertFrom-Csv -Delimiter '|')
$sources = @($registry.sources)
if ($sources.Count -ne 189 -or $decisions.Count -ne 189) { throw 'Expected the reviewed 189-record snapshot and 189 explicit AI-agent decisions.' }
if (@($decisions.id | Sort-Object -Unique).Count -ne 189) { throw 'Duplicate decision IDs.' }
$difference = @(Compare-Object @($sources.id | Sort-Object) @($decisions.id | Sort-Object))
if ($difference.Count) { throw 'Decision/source ID mismatch.' }

$roles = [ordered]@{
 P = 'physical_environment_measurement'
 T = 'operational_telemetry'
 H = 'human_sample_lab_observation'
 D = 'model_forecast_derived_product'
 C = 'documentary_spatial_context'
 M = 'mixed_insufficient'
}
$iot = [ordered]@{
 D = 'networked_sensing_telemetry_documented'
 C = 'candidate_not_proven'
 N = 'contextual_non_iot'
 X = 'no_local_coverage'
}
$coverage = [ordered]@{
 L = 'explicit_local_site_or_product_applicability'
 B = 'bounding_box_scope_not_administrative_city'
 R = 'regional_national_or_global_context'
 G = 'local_presence_or_selected_product_unverified'
 U = 'publication_or_access_gap_not_geographic_absence'
 X = 'scope_specific_local_noncoverage_recorded'
 I = 'local_spatial_coverage_inferred_not_verified'
}
$decisionById = @{}
foreach ($d in $decisions) { $decisionById[$d.id] = $d }
$supplements = @{
 S57 = @('research/observations/putevi-aadt/putevi_aadt_2018_2024.csv')
 S102 = @('research/02-senses/GROUND_CURRENT_PRODUCTS_2026-09-06.md','research/02-senses/CURRENT_PRODUCTS_2026-09-06.md')
 S158 = @('research/04-bibliography/LITERATURE_GROUND_EMF_2026-09-06.md','research/02-senses/CURRENT_PRODUCTS_2026-09-06.md')
 S175 = @('research/02-senses/DEVICE_PROCUREMENT_2026-09-06.md','research/04-bibliography/LITERATURE_INFRASTRUCTURE_2026-09-06.md')
 S184 = @('research/02-senses/DEVICE_PROCUREMENT_2026-09-06.md')
 S186 = @('research/02-senses/DEVICE_HYDROMET_2026-09-06.md','research/02-senses/ACTRIS_PRODUCT_2026-09-06.md')
 S187 = @('research/02-senses/DEVICE_HYDROMET_2026-09-06.md')
 S188 = @('research/02-senses/DEVICE_HYDROMET_2026-09-06.md')
 S189 = @('research/02-senses/DEVICE_PROCUREMENT_2026-09-06.md')
 S191 = @('research/02-senses/ADA_DATA_ACCESS_2026-09-06.md','research/_trail/ADA_DATA_ACCESS_2026-09-06.json','research/02-senses/CURRENT_PRODUCTS_2026-09-06.md')
 S192 = @('research/02-senses/CURRENT_PRODUCTS_2026-09-06.md','research/02-senses/GROUND_CURRENT_PRODUCTS_2026-09-06.md')
}
$projectRoot = Split-Path -Parent (Split-Path -Parent $RegistryPath)
function Convert-EvidenceReferenceToPath([string]$reference) {
 $p = $reference.Replace('\','/').Trim()
 $rootPrefix = $projectRoot.Replace('\','/').TrimEnd('/')+'/'
 if ($p.StartsWith($rootPrefix)) { $p = $p.Substring($rootPrefix.Length) }
 if ($p.StartsWith('evidence/')) { $p = 'research/'+$p }
 if ($p -match '^(research/08-provenance/)\s+\(') { $p = $Matches[1] }
 return $p
}
$relatedBasis = @{ S02=@('S01'); S05=@('S50'); S21=@('S106'); S24=@('S34'); S50=@('S05'); S111=@('S19') }
$overlapGroups = [ordered]@{
 rhmz_surface_routes = @('S01','S02')
 beoeko_routes = @('S05','S50')
 possible_air_station_lineage = @('S05','S06','S49','S50','S146')
 possible_citizen_sensor_overlap = @('S04','S24','S34')
 rhmz_river_routes = @('S09','S52')
 planned_electricity_notices = @('S12','S54')
 local_seismic_metadata_waveform_routes = @('S19','S111')
 serbian_seismic_catalogue_routes = @('S16','S53')
 emsc_catalogue_routes = @('S17','S84')
 possible_raspberry_shake_overlap = @('S20','S183')
 amss_naxi_camera_routes = @('S21','S106')
 windy_camera_routes = @('S22','S107')
 imerg_routes = @('S25','S90')
 firms_routes = @('S26','S89')
 sentinel2_routes = @('S27','S109')
 apr_registry_routes = @('S30','S43','S149')
 osm_extract_routes = @('S33','S127')
 gbif_routes = @('S41','S177')
 procurement_routes = @('S42','S156')
 possible_openaq_routes = @('S08','S101')
 possible_pollen_lineage = @('S152','S157')
 ada_aerosol_literature_and_catalogue = @('S190','S191')
}
$remote = @('S25','S26','S27','S58','S88','S89','S90','S109','S110','S181')
$roleBoundaries = @('S57','S85','S115','S126','S139','S153','S155','S175','S176','S184','S190','S191')
$geographicMisuse = @('S63','S64','S125','S132')
$historical = @('S06','S57','S65','S100','S111','S123','S124','S158','S175','S186','S187','S188','S189','S190','S191')
$strictArchitectureSensitivity = @('S01','S02','S05','S24','S49','S50','S91','S146','S188')
$records = @()
for ($index=0; $index -lt $sources.Count; $index++) {
 $s = $sources[$index]
 $d = $decisionById[$s.id]
 if (-not $roles.Contains($d.role) -or -not $iot.Contains($d.iot) -or -not $coverage.Contains($d.coverage)) { throw ('Invalid code for '+$s.id) }
 $flags = @()
 if ($d.role -eq 'M') { $flags += 'split_product_family_before_quantitative_use' }
 if ($d.iot -eq 'D') { $flags += 'documented_chain_is_not_current_uptime_or_device_count' }
 if ($d.iot -eq 'C') { $flags += 'network_architecture_or_local_identity_unresolved' }
 if ($d.iot -eq 'X') { $flags += 'scope_specific_negative_finding_not_citywide_absence' }
 if ($d.coverage -eq 'B') { $flags += 'bbox_is_not_city_boundary' }
 if ($d.coverage -in @('G','I')) { $flags += 'local_product_or_site_not_verified' }
 if ($s.id -in $remote) { $flags += 'remote_observation_or_physical_retrieval_not_local_iot_deployment' }
 if ($s.id -in $roleBoundaries) { $flags += 'role_boundary_or_heterogeneous_origin_requires_review' }
 if ($s.id -in $geographicMisuse) { $flags += 'original_no_coverage_status_is_not_geographic_absence' }
 if ($s.id -in $historical) { $flags += 'historical_or_archive_evidence_not_present_operation' }
 if ($s.id -in $strictArchitectureSensitivity) { $flags += 'eligibility_sensitive_to_stricter_iot_architecture_definition' }
 if ($s.status -in @('blocked','opted_out','restricted','token_required','account_required','needs_decision')) { $flags += 'original_access_or_legal_hold_preserved' }
 if (($s.rhythm -match '(?i)\blive\b|real.time|continuous') -or ($s.next -match '(?i)\blive\b')) { $flags += 'inherited_temporal_wording_not_revalidated' }
 $groups = @($overlapGroups.Keys | Where-Object { $s.id -in $overlapGroups[$_] })
 if ($groups.Count) { $flags += 'overlap_group_not_independent_device_count' }
 $evidencePaths = @('research/SOURCE_REGISTRY.json#/sources/'+$index)
 $originalReferences = @()
 if ($s.evidence) { $originalReferences += [string]$s.evidence; $evidencePaths += Convert-EvidenceReferenceToPath ([string]$s.evidence) }
 if ($s.provenance_capture) { $originalReferences += [string]$s.provenance_capture; $evidencePaths += Convert-EvidenceReferenceToPath ([string]$s.provenance_capture) }
 if ($s.raw_response) { $originalReferences += [string]$s.raw_response; $evidencePaths += Convert-EvidenceReferenceToPath ([string]$s.raw_response) }
 if ($supplements.ContainsKey($s.id)) { $evidencePaths += $supplements[$s.id] }
 $basisIds = @()
 if ($relatedBasis.ContainsKey($s.id)) { $basisIds = $relatedBasis[$s.id] }
 $records += [ordered]@{
  id=$s.id
  name=$s.name
  url=$s.url
  original_theme=$s.theme
  original_status=$s.status
  original_kind=$s.kind
  source_role=$roles[$d.role]
  iot_eligibility=$iot[$d.iot]
  coverage_scope=$coverage[$d.coverage]
  coding_reason=$d.reason
  registry_pointer=('/sources/'+$index)
  registry_fields_used=@('name','kind','rhythm','access','next','measurement_time','evidence')
  original_evidence_assertions=[ordered]@{rhythm=$s.rhythm; access=$s.access; measurement_time=$s.measurement_time; device_evidence=$s.device_evidence}
  evidence_paths=@($evidencePaths | Select-Object -Unique)
  original_evidence_reference_text=$originalReferences
  evidence_read_scope='Registry assertions and selected identified dossiers. Raw/provenance paths are traceability references, not a claim that every referenced file was reread.'
  related_registry_evidence_ids=$basisIds
  ambiguity_flags=@($flags | Select-Object -Unique)
  overlap_groups=$groups
  current_operation_newly_verified=$false
  legal_or_collection_authorization_changed=$false
 }
}
$roleCounts = [ordered]@{}
foreach ($v in $roles.Values) { $roleCounts[$v] = @($records | Where-Object source_role -eq $v).Count }
$iotCounts = [ordered]@{}
foreach ($v in $iot.Values) { $iotCounts[$v] = @($records | Where-Object iot_eligibility -eq $v).Count }
$cross = @()
foreach ($r in $roles.Values) {
 $row = [ordered]@{source_role=$r; total=$roleCounts[$r]}
 foreach ($v in $iot.Values) { $row[$v] = @($records | Where-Object { $_.source_role -eq $r -and $_.iot_eligibility -eq $v }).Count }
 $cross += $row
}
$result = [ordered]@{
 schema='beops-registry-desk-coding/v1'
 reviewed_at='2026-09-06'
 status='complete_ai_agent_desk_coding_pending_coordinator_review'
 coder_kind='Explicit AI-agent desk coding by Codex hydromet; not human coding and not an independent multi-coder reliability study.'
 purpose='Evidence-atlas and pre-paper discussion input for urban information, pattern and planning questions; IoT evidence is a secondary dimension. No manuscript is drafted by these artifacts.'
 unit_of_analysis='One existing registry record, not a device, installation, provider, endpoint, dataset, independent observation or live feed.'
 input=[ordered]@{path='research/SOURCE_REGISTRY.json'; sha256=(Get-FileHash -LiteralPath $RegistryPath -Algorithm SHA256).Hash.ToLowerInvariant(); records=189; registry_reviewed_at=$registry.reviewed_at; decision_file='research/_trail/PAPER_CODING_DECISIONS_2026-09-06.psv'; decision_sha256=(Get-FileHash -LiteralPath $decisionsPath -Algorithm SHA256).Hash.ToLowerInvariant(); build_script='research/build_paper_registry_coding_20260906.ps1'; evidence_path_base='Beops project root; all evidence_paths are project-relative, with optional JSON fragments.'}
 codebook=[ordered]@{
  assignment='All 189 AI-agent desk decisions are explicit in the companion decision file. No keyword classifier or fallback category assigns records. The build script validates exact ID coverage and only generates artifacts/counts.'
  source_role_definitions=[ordered]@{
   physical_environment_measurement='An instrument-facing observation product or documented measurement chain, including calibrated remote observations and physical retrievals. Simple averaging/validation does not alone turn it into a model.'
   operational_telemetry='Machine/system operational state or event telemetry, including occupancy and network/vehicle operation. An unproven acquisition chain remains visible in the separate eligibility field.'
   human_sample_lab_observation='Observer, specimen, sampled or laboratory evidence; internet publication alone is not proof of connected sensing.'
   model_forecast_derived_product='Explicit forecast, reanalysis, hazard/likelihood model, thematic classification or synthesized derived spatial indicator. Observation-linked physical retrievals remain physical with a caveat.'
   documentary_spatial_context='Notices, schedules, registers, legal/administrative statistics, maps, reference geometry and discovery/publication records. Planned or mapped events are not automatically observed physical events.'
   mixed_insufficient='A record spans materially different roles, or its current evidence cannot isolate a defensible single dominant role. Split into product-level units before quantitative inference.'
  }
  iot_eligibility_definitions=[ordered]@{
   networked_sensing_telemetry_documented='At least one locally grounded electronic sensing/telemetry chain is documented: a named automatic network with local station observations/metadata, an explicit remote-monitoring chain, or a connected camera/radio/network-probe system. Architecture, identity and present uptime are not certified. Historical and mixed-record subchains are expressly marked.'
   candidate_not_proven='A sensing/telemetry candidate exists, but the local identity or network connection is not sufficiently established; a publication API, archive, sampler or instrument label alone does not settle this.'
   contextual_non_iot='Useful contextual input for the city study without a demonstrated local IoT deployment in this record, including satellite products, models, human/lab observations, documents and country-level aggregates. This is not a universal claim about the provider technology.'
   no_local_coverage='A scoped negative finding is recorded for an exact catalogue, product/vintage or search rectangle. It does not imply that the phenomenon, all devices or all alternative services are absent.'
  }
  rules=@('Read functional product/evidence role separately from byte access and current freshness.','Use the original snapshot and identified supplemental dossiers; do not infer deployment from a tender, licence, HTTP success or update cadence.','Keep a failed tool/server/access route distinct from geographic absence.','Retain physical satellite observations while excluding them from local ground-IoT deployment eligibility.','Mixed sources stay mixed; no majority or one-provider-one-device assumption.','A paper or local observation confirms only its stated time/site/chain; no current-operation inference.','All original themes/statuses remain copied verbatim; this desk coding does not revalidate earlier factual or legal assertions.','Documented IoT eligibility is definition-sensitive and is not the primary success metric of the broader planning study.')
 }
 summary=[ordered]@{record_count=189; source_role_counts=$roleCounts; iot_eligibility_counts=$iotCounts; cross_tabulation=$cross; strict_architecture_review_ids=$strictArchitectureSensitivity; mixed_record_ids=@($records | Where-Object source_role -eq 'mixed_insufficient' | ForEach-Object id); scope_specific_negative_ids=@($records | Where-Object iot_eligibility -eq 'no_local_coverage' | ForEach-Object id); original_no_coverage_not_geographic_ids=$geographicMisuse}
 overlap_groups=$overlapGroups
 overlap_limit='Groups are a non-exhaustive review aid, not a completed provider/measurement deduplication or equivalence relation.'
 records=$records
 limits=@('Convenience research register, not a systematic city device census or representative sampling frame.','No new network requests, raw data, login, institutional contacts or changes to D: files.','No uptime, current live-feed count, device count, city intelligence score or tested big-data scalability claim.','No inter-rater reliability coefficient: this is one explicit coding pass awaiting coordinator review.','API/publication status, file accessibility, instrument existence, observation freshness and reuse permission remain different dimensions.','Broad bbox results may include places outside administrative Belgrade.','Inherited statements such as global closures or live wording have not all been independently reverified in this coding pass.')
}
$outputPath = Join-Path $OutputDirectory 'PAPER_REGISTRY_CODING_2026-09-06.json'
$result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $outputPath -Encoding utf8
$reloaded = Get-Content -LiteralPath $outputPath -Raw | ConvertFrom-Json
if ($reloaded.records.Count -ne 189) { throw 'Output count mismatch.' }
if (($roleCounts.Values | Measure-Object -Sum).Sum -ne 189 -or ($iotCounts.Values | Measure-Object -Sum).Sum -ne 189) { throw 'Count denominator mismatch.' }
$result.summary | ConvertTo-Json -Depth 10
