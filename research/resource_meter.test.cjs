'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {Meter,withMeter,tokenUsage,httpAttempt,httpBody}=require('../tools/resource_meter');
const {buildSummary}=require('../tools/resource_summary');
const ROOT=path.resolve(__dirname,'..');fs.mkdirSync(path.join(ROOT,'runtime'),{recursive:true});
const root=fs.mkdtempSync(path.join(ROOT,'runtime/resource-test-'));
function write(relative,value){const p=path.join(root,relative);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,JSON.stringify(value));}
async function main(){
  assert.equal(tokenUsage(null).input_tokens,null);
  assert.equal(tokenUsage({input_tokens:'12'}).input_tokens,null);
  assert.equal(tokenUsage({input_tokens:-1}).input_tokens,null);
  const gemini=tokenUsage({promptTokenCount:12,candidatesTokenCount:4,thoughtsTokenCount:7,totalTokenCount:23});
  assert.equal(gemini.output_tokens,4);assert.equal(gemini.reasoning_tokens,7);assert.equal(gemini.provider_total_tokens,23);
  const claude=tokenUsage({input_tokens:4,output_tokens:5,cache_read_input_tokens:11,cache_creation_input_tokens:3});
  assert.equal(claude.input_tokens,4);assert.equal(claude.cached_input_tokens,11);assert.equal(claude.provider_total_tokens,null);
  // Actual returned CLI usage shapes (only numerical usage, no prompts or response text).
  // Antigravity receipt 1e0aeda96b475f99ca6140a2910160e4: cache can exceed input.
  const agy=tokenUsage({input_tokens:44037,output_tokens:18922,thinking_tokens:17994,cache_read_tokens:63404,total_tokens:62959});
  assert.equal(agy.input_tokens,44037);assert.equal(agy.output_tokens,18922);
  assert.equal(agy.cached_input_tokens,63404);assert.equal(agy.reasoning_tokens,17994);
  assert.equal(agy.provider_total_tokens,62959);assert.equal(agy.cache_creation_input_tokens,null);
  // Codex receipt 05c1950825bd26c1e7b41d11de1c4881 has no provider total.
  const codex=tokenUsage({input_tokens:12072,cached_input_tokens:0,cache_write_input_tokens:0,output_tokens:428,reasoning_output_tokens:175});
  assert.equal(codex.input_tokens,12072);assert.equal(codex.output_tokens,428);
  assert.equal(codex.reasoning_tokens,175);assert.equal(codex.cache_creation_input_tokens,0);
  assert.equal(codex.cached_input_tokens,0);assert.equal(codex.provider_total_tokens,null);
  const cacheWrite=tokenUsage({input_tokens:4,output_tokens:5,cache_write_input_tokens:7});
  assert.equal(cacheWrite.input_tokens,4);assert.equal(cacheWrite.cache_creation_input_tokens,7);
  assert.equal(cacheWrite.provider_total_tokens,null);
  const canonicalZero=tokenUsage({input_tokens:1,output_tokens:1,cached_input_tokens:0,cache_read_tokens:5,
    output_tokens_details:{reasoning_tokens:0},reasoning_output_tokens:7,thinking_tokens:8,
    cache_creation_input_tokens:0,cache_write_input_tokens:9});
  assert.equal(canonicalZero.cached_input_tokens,0);assert.equal(canonicalZero.reasoning_tokens,0);
  assert.equal(canonicalZero.cache_creation_input_tokens,0);
  for(const usage of [{thinking_tokens:-1},{reasoning_output_tokens:'7'},{cache_read_tokens:1.5},{cache_write_input_tokens:Infinity}]){
    const invalid=tokenUsage(usage);
    assert.equal(invalid.reasoning_tokens,null);assert.equal(invalid.cached_input_tokens,null);
    assert.equal(invalid.cache_creation_input_tokens,null);assert.equal(invalid.provider_total_tokens,null);
    assert.equal(invalid.state,'unavailable');
  }
  const result=await withMeter(root,'ai_feed',async meter=>{
    const call=meter.providerAttempt();meter.providerResponse(call,{usage:{input_tokens:7,output_tokens:3}});
    meter.providerAttempt(); // a timeout can cost tokens without returning usage
    httpBody(httpAttempt(),32);httpAttempt();
    return {state:'failed'};
  });assert.equal(result.state,'failed');
  const unfinished=new Meter(root,'collection');
  const report=buildSummary(root);
  assert.equal(report.windows.day.started_cycles,2);assert.equal(report.windows.day.finished_cycles,1);
  assert.equal(report.windows.day.unfinished_cycles,1);
  assert.equal(report.windows.day.tokens.input_tokens,7);assert.equal(report.windows.day.tokens.unreported_calls,1);
  assert.equal(report.windows.day.response_body_bytes,32);assert.equal(report.windows.day.unreported_bodies,1);
  assert.equal(report.electricity.wh,null);assert.equal(report.money.amount,null);
  assert.ok(report.windows.day.cpu_seconds>=0);assert.ok(report.windows.day.peak_rss_bytes>0);
  unfinished.finish('failed');
  assert.throws(()=>unfinished.finish(),/EEXIST/); // immutable finish cannot change
  await assert.rejects(withMeter(root,'collection',async()=>{throw Error('test_failure');}),/test_failure/);
  const id='a'.repeat(32),at=new Date().toISOString();
  write('runtime/ai-feed/receipts/2026-'+id+'-start.json',{id,at,provider:'test',model:'fixture',state:'started'});
  write('runtime/ai-feed/receipts/2026-'+id+'-finish.json',{id,at,provider:'test',model:'fixture',state:'failed'});
  write('runtime/ai-feed/responses/'+id+'.json',{usage:{input_tokens:100,output_tokens:20,thinking_tokens:12,cache_read_tokens:50}});
  const second=buildSummary(root);
  assert.equal(second.historical_provider_usage.all.attempts,1);
  assert.equal(second.historical_provider_usage.all.input_tokens,100);
  assert.equal(second.historical_provider_usage.all.output_tokens,20);
  assert.equal(second.historical_provider_usage.all.reasoning_tokens,12);
  assert.equal(second.historical_provider_usage.all.cached_input_tokens,50);
  assert.equal(second.historical_provider_usage.all.provider_total_tokens,null);
  assert.equal(second.historical_provider_usage.all.outcomes.failed,1);
  assert.equal(second.windows.day.tokens.input_tokens,7); // historical does not inflate current metering
  assert.equal(second.windows.day.tokens.reasoning_tokens,null); // immutable cycle values stay as recorded
  const prior=new Date(Date.now()-8*86400000),third='b'.repeat(32);
  write('runtime/resources/receipts/'+third+'-start.json',{schema:'beops-resource-cycle/v1',id:third,activity:'collection',phase:'start',started_at:prior.toISOString()});
  const last=buildSummary(root);assert.equal(last.windows.month.started_cycles,last.windows.week.started_cycles+1);
  assert.equal(last.windows.month.unfinished_cycles,1);
  const future=new Date(Date.now()+86400000),orphan='c'.repeat(32);
  write('runtime/resources/receipts/'+orphan+'-finish.json',{schema:'beops-resource-cycle/v1',id:orphan,phase:'finish',started_at:at,finished_at:at});
  const malformed='d'.repeat(32);
  write('runtime/resources/receipts/'+malformed+'-start.json',{schema:'beops-resource-cycle/v1',id:'e'.repeat(32),phase:'start',started_at:at});
  assert.equal(buildSummary(root).coverage.incomplete_receipts,2);
  const late=new Meter(root,'collection');
  const lateFinish=late.finish();
  write('runtime/resources/receipts/'+lateFinish.id+'-finish.json',{...lateFinish,finished_at:future.toISOString()});
  assert.equal(buildSummary(root).windows.day.unfinished_cycles,1);
  write('runtime/ai-feed/receipts/2027-'+'f'.repeat(32)+'-start.json',{id:'f'.repeat(32),at:future.toISOString(),provider:'test',state:'started'});
  assert.equal(buildSummary(root).historical_provider_usage.all.attempts,1);
  // Earliest Python receipts used null for calls even in paths that never invoke AI.
  // Preserve those immutable records, but do not label collection/calendar as unknown AI work.
  for(const [digit,activity,state] of [['1','collection','not_applicable'],['2','calendar','not_applicable'],['3','news','not_instrumented'],['4','mind','not_instrumented']]){
    const cycle={schema:'beops-resource-cycle/v1',id:digit.repeat(32),phase:'start',started_at:at,activity,pid:42,runtime:'python'};
    write('runtime/resources/receipts/'+cycle.id+'-start.json',cycle);
    write('runtime/resources/receipts/'+cycle.id+'-finish.json',{...cycle,phase:'finish',finished_at:at,outcome:'completed',wall_seconds:1,cpu_seconds:0.1,peak_rss_bytes:null,
      http:{request_attempts:0,response_body_bytes:0,body_reports:0,unreported_bodies:0},
      tokens:{state,reported_calls:0,unreported_calls:null,input_tokens:null,output_tokens:null,cached_input_tokens:null}});
  }
  const mixed=buildSummary(root).windows.day;
  assert.equal(mixed.tokens.unknown_call_count_cycles,2);
  assert.equal(mixed.activities.find(x=>x.activity==='calendar').tokens.unknown_call_count_cycles,0);
  assert.equal(mixed.activities.find(x=>x.activity==='collection').tokens.unknown_call_count_cycles,0);
  assert.equal(mixed.activities.find(x=>x.activity==='news').tokens.unknown_call_count_cycles,1);
  assert.equal(mixed.activities.find(x=>x.activity==='mind').tokens.unknown_call_count_cycles,1);
  const broken={schema:'beops-resource-cycle/v1',id:'5'.repeat(32),phase:'start',started_at:at,activity:'collection',pid:42,runtime:'python'};
  write('runtime/resources/receipts/'+broken.id+'-start.json',broken);
  write('runtime/resources/receipts/'+broken.id+'-finish.json',{...broken,phase:'finish',finished_at:at,wall_seconds:1,cpu_seconds:0.1});
  const missingFields=buildSummary(root);
  assert.equal(missingFields.coverage.incomplete_receipts,3);
  assert.equal(missingFields.windows.day.unfinished_cycles,2);
  const pending='6'.repeat(32);
  write('runtime/ai-feed/receipts/2026-'+pending+'-start.json',{id:pending,at,provider:'test',state:'started'});
  write('runtime/ai-feed/receipts/2026-'+pending+'-finish.json',{id:pending,at:future.toISOString(),provider:'test',state:'accepted'});
  write('runtime/ai-feed/responses/'+pending+'.json',{usage:{input_tokens:999,output_tokens:999}});
  const historicalCut=buildSummary(root).historical_provider_usage.all;
  assert.equal(historicalCut.attempts,2);assert.equal(historicalCut.outcomes.started,1);
  assert.equal(historicalCut.input_tokens,100);assert.equal(historicalCut.unreported_calls,1);
  console.log('resource meter offline contracts passed');
}
main().finally(()=>fs.rmSync(root,{recursive:true,force:true})).catch(error=>{console.error(error);process.exitCode=1;});
