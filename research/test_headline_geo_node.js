'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {locateHeadline:locate,normalize,GAZETTEER}=require('../tools/headline_geo');

test('script, inflection and row fields preserve explicit Belgrade place',()=>{
  for(const headline of ['Radovi na Novom Beogradu','РАДОВИ НА НОВОМ БЕОГРАДУ',{result:'Srbijagas: Danas od 8 do 20 časova prekid isporuke gasa za kupce na Novom Beogradu'}]){
    const r=locate(headline);assert.equal(r.scope,'belgrade');assert.equal(r.status,'estimated');assert.equal(r.estimate.name,'Novi Beograd');assert.ok(r.estimate.radius_m>1000);assert.equal(r.candidates.filter(c=>c.place_id==='beograd').length,0);
  }
  assert.equal(normalize('Ђорђе ЋИРИЛИЦА'),'djordje cirilica');
});
test('spatial precision changes radius, nearby is explicitly coarser',()=>{
  const city=locate('Kakav je kvalitet vazduha u Beogradu'),area=locate('Požar na Dorćolu'),near=locate('Požar kod Dorćola');
  assert.equal(city.estimate.precision,'city');assert.ok(city.estimate.radius_m>area.estimate.radius_m);assert.equal(near.estimate.radius_m,area.estimate.radius_m*2);assert.equal(area.estimate.verified,false);assert.equal(typeof area.estimate.confidence,'string');
});
test('national and foreign titles never become Belgrade measurements',()=>{
  for(const h of ['Zagađen vazduh u Nišu','Saobraćajna nesreća u Novom Sadu','Srbija beleži rast cena'])assert.equal(locate(h).scope,'serbia');
  for(const h of ['Požar u Parizu','Rusija napala Ukrajinu','Snažno nevreme u Sarajevu']){assert.equal(locate(h).scope,'outside');assert.equal(locate(h).estimate,null);}
  assert.equal(locate('Cene goriva rastu').scope,'unknown');assert.equal(locate('Prvi put sad nastupa ovde').scope,'unknown');
});
test('homonyms require a direct local qualifier, never publisher or personal origin',()=>{
  for(const h of ['Na Paliluli dva muškarca ubodena nožem, jedan povređen u tuči','Požar u Starom gradu','Trener iz Beograda govori o nesreći na Paliluli','Požar u Starom gradu u Sarajevu'])assert.equal(locate(h).estimate,null,h);
  assert.equal(locate({title:'Požar na Paliluli',source:'Beograd danas'}).estimate,null);
  assert.equal(locate('Požar na beogradskoj Paliluli').estimate.name,'Palilula');
  assert.equal(locate('Požar na Paliluli u Beogradu').estimate.name,'Palilula');
});
test('multiple locations and routes keep alternatives, never a synthetic point',()=>{
  for(const h of ['Radovi na Novom Beogradu i u Zemunu','Radovi na Novom Beogradu i Zemunu','Bez vode danas deo potrošača na Paliluli i Zvezdari','Zatvoren put Beograd–Niš','Požar u Beogradu i u Parizu','KOMFOR U GRADSKOM PREVOZU: Putnici ne kriju zadovoljstvo novim autobusima na Paliluli, u Obrenovcu i Surčinu']){
    const r=locate(h);assert.equal(r.estimate,null,h);assert.equal(r.status,'ambiguous',h);assert.ok(r.candidates.length>1,h);
  }
});
test('coordinated foreign cities and country scopes inherit a spatial cue',()=>{
  for(const h of ['Ursula fon der Lajen ipak ne dolazi u Beograd i Sarajevo u oktobru','Studentska lista predstavlja plan u Beogradu i u centralnoj Srbiji','Predstava u Zemunu i Londonu','Koncerti u Zemunu i u celoj Srbiji','Koncerti u Beogradu i centralnoj Srbiji','Predstave u Beogradu, Sarajevu']){
    const r=locate(h);assert.equal(r.estimate,null,h);assert.equal(r.status,'ambiguous',h);
  }
  const institutional=locate('Institut za transfuziju krvi Srbije organizuje akciju u Zemunu');assert.equal(institutional.estimate.name,'Zemun');
  assert.equal(locate('Muškarac iz Beograda povređen u Nišu').scope,'serbia');
});
test('origin, metonymy, organizations and clubs are mentions only',()=>{
  for(const h of ['Beograd poručuje Prištini da nastavi dijalog','Pobeda Novog Beograda u finalu','Novi Beograd pobedio Partizan','Saopštenje FK Zemun','U NIS-u otkazi','Igrač iz Zemuna dobio nagradu','Nesreća u ulici Novi Beograd'])assert.equal(locate(h).estimate,null,h);
});
test('institution affiliation, longer place name and roundups cannot shrink to a wrong event site',()=>{
  for(const h of ['Ambasada Francuske u Srbiji osudila napad na dekana Filozofskog fakulteta u Beogradu','Noć u Beogradu: Žena teško povređena ubadanjem u stomak u Zemun polju, dečak pao s motora','Hitna pomoć: Tokom noći u Beogradu jedna saobraćajna nezgoda, na Paliluli muškarac pao sa bicikla'])assert.equal(locate(h).estimate,null,h);
  assert.equal(locate('Požar u Zemun polju').estimate.name,'Zemun Polje');
  assert.equal(locate('Požar u Zemun polju').candidates.some(c=>c.place_id==='zemun'),false);
  assert.equal(locate('Radovi na Paliluli u Beogradu').estimate.name,'Palilula');
});

test('retained coordinates extend suburbs and national cities without crossing scopes',()=>{
  for(const [headline,name,scope] of [
    ['Muškarac pao sa velike visine u Batajnici','Batajnica','belgrade'],
    ['Jesenje prelo u Surčinu','Surčin','belgrade'],
    ['Pas napao devojčicu u Barajevu','Barajevo','belgrade'],
    ['Sudar autobusa i vozila auto-škole u Mladenovcu','Mladenovac','belgrade'],
    ['Radovi na grejanju u Grockoj','Grocka','belgrade'],
    ['Užas u Novom Sadu: Posle pucanja plinske boce planuo požar','Novi Sad','serbia'],
    ['Mobilni mamograf u Pančevu','Pančevo','serbia'],
    ['U Kragujevcu pripreme za doček studenata danas','Kragujevac','serbia']
  ]){const r=locate(headline);assert.equal(r.estimate.name,name);assert.equal(r.scope,scope);assert.equal(r.estimate.verified,false);assert.match(r.estimate.evidence.capture,/headline-geo-20260927-v2/);}
  for(const headline of ['Požar u Obrenovcu','Nesreća u Lazarevcu','Požar u Subotici','Požar u Leskovcu'])assert.equal(locate(headline).estimate,null,headline);
});

test('one-city transit changes keep their broad place, routes keep alternatives',()=>{
  for(const [headline,name] of [
    ['Velike izmene prevoza u Beogradu: Ukidaju se tramvaji, menjaju trase brojnih linija','Beograd'],
    ['ZATVARANJE VIŠE ULICA NA NOVOM BEOGRADU Zbog radova dve linije javnog prevoza menjaju trasu i okretnicu','Novi Beograd'],
    ['Linija 64 menja trasu zbog radova na Zvezdari','Zvezdara']
  ]){assert.equal(locate(headline).estimate.name,name);assert.ok(locate(headline).estimate.radius_m>=5000);}
  for(const headline of ['Menja se trasa od Beograda do Novog Sada','Zatvorena deonica kod Beograda','Radovi između Beograda i Smederevske Palanke'])assert.equal(locate(headline).estimate,null,headline);
});

test('previously unknown secondary places block a misleading single-city estimate',()=>{
  for(const headline of [
    'Kako se živi u đačkim domovima u Požarevcu i Kostolcu?',
    'Katastri u Boru, Majdanpeku, Boljevcu i Donjem Milanovcu neće raditi',
    'Rumunska ministarka tražila konsultacije o rudnicima kod Bora i Majdanpeka',
    'Uhapšena jedna osoba zbog više krađa u Sremskoj Mitrovici i Rumi',
    'Više požara na Fruškoj gori i u okolini Sremske Mitrovice',
    'Isključenja struje u čak pet opština u Beogradu: Isključenja najduža u Surčinu'
  ]){const r=locate(headline);assert.equal(r.estimate,null,headline);assert.ok(r.candidates.length>=2,headline);}
});

test('court and faculty affiliations are not promoted to crime or competition locations',()=>{
  for(const headline of [
    'Apelacioni sud u Kragujevcu odlučuje o slučaju ubistva bračnog para u Arilju',
    'VJT u Pančevu: Određen pritvor osumnjičenom da je u Starčevu aktivirao bombu',
    'Studenti PMF-a u Novom Sadu osvojili sedmo mesto na prestižnom svetskom takmičenju',
    'Suđenje vlasnicima doma za stare u Barajevu; svedok kaže da je objekat ranije trebalo zatvoriti',
    'VJT u Beogradu: Nije bilo zvučnog topa 15. marta'
  ])assert.equal(locate(headline).estimate,null,headline);
  assert.equal(locate('U Novom Sadu studenti PMF-a organizuju skup').estimate.name,'Novi Sad');
});
test('every drawn coordinate is traceable to retained OSM evidence',()=>{
  assert.ok(GAZETTEER.places.length>=20);
  const captures=new Map();
  for(const p of GAZETTEER.places.filter(p=>p.lon!=null)){
    const file=path.join(__dirname,'..',p.evidence.capture);let raw=captures.get(file);if(!raw){raw=fs.readFileSync(file);captures.set(file,raw);}
    assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),p.evidence.raw_sha256);
    const [type,id]=p.evidence.source_url.split('/').slice(-2);const e=JSON.parse(raw).elements.find(e=>e.type===type&&String(e.id)===id);assert.ok(e);assert.equal((e.center||e).lon,p.lon);assert.equal((e.center||e).lat,p.lat);assert.ok(p.radius_m>0);
  }
});
test('batch CLI accepts UTF8 row and string input without network',()=>{
  const r=spawnSync(process.execPath,['tools/headline_geo.js','--json'],{cwd:path.join(__dirname,'..'),input:JSON.stringify(['Radovi u Beogradu',{result:'Požar u Nišu'}]),encoding:'utf8',windowsHide:true});assert.equal(r.status,0,r.stderr);const results=JSON.parse(r.stdout);assert.equal(results.length,2);assert.equal(results[0].scope,'belgrade');assert.equal(results[1].scope,'serbia');
});
