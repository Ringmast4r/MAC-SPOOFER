'use strict';
let intelAdviceKey='', intelAdviceSerial=0, intelSearchSerial=0, intelLookupSerial=0, intelProfileSerial=0;
let intelOrigin='User-entered sequence';
const intelNumber=value=>Number(value||0).toLocaleString();
window.refreshIntelligence=async function(){
  if(!state)return;
  const meta=state.intelligence||{};
  $('intel-counts').textContent=meta.available?`${intelNumber(meta.signatures)} indexed sequences · ${intelNumber(meta.rules)} association rules · ${intelNumber(meta.label_prefixes)} OUI-linked corpus labels`:'Offline Huginn–Muninn index unavailable.';
  $('intel-quality').textContent=meta.available?`${intelNumber(meta.signature_source_rows)} source signature rows; ${intelNumber(meta.invalid_signatures)} malformed and ${intelNumber(meta.ignored_signatures)} ignored rows excluded. ${intelNumber(meta.duplicate_signatures)} duplicates consolidated. Indexed means syntactically valid, not confirmed identification.`:'';
  const adapter=current(), entered=$('candidate').value.trim();
  const mac=entered?candidate?.mac:adapter?.mac;
  if(!mac){$('advice-content').textContent=entered?'Enter a valid candidate to see selection guidance.':'Select an adapter or prepare an address.';intelAdviceKey='';intelAdviceSerial++;return;}
  const key=JSON.stringify([mac,adapter?.id,state.adapters.map(a=>[a.id,a.mac])]);
  if(key===intelAdviceKey)return;
  intelAdviceKey=key;const serial=++intelAdviceSerial;
  try{
    const info=await api('advice?mac='+encodeURIComponent(mac)+'&adapter='+encodeURIComponent(adapter?.id||''));
    if(serial!==intelAdviceSerial)return;
    $('advice-content').innerHTML=`<p class="advice-address">${entered?'PREPARED':'CURRENT'} ADDRESS · ${escapeHTML(info.mac)}</p><strong class="advice-title ${escapeHTML(info.tone)}">${escapeHTML(info.title)}</strong>${info.issues.length?'<ul>'+info.issues.map(v=>'<li>'+escapeHTML(v)+'</li>').join('')+'</ul>':''}<p>${escapeHTML(info.compatibility)}</p>${info.registered_owner?'<p><b>OUI registration:</b> '+escapeHTML(info.registered_owner)+'</p>':''}${info.corpus_labels.length?'<p><b>Huginn–Muninn label:</b> '+escapeHTML(info.corpus_labels.join(' / '))+' <span class="muted">(parent prefix; corroborating label only)</span></p>':''}<p>${escapeHTML(info.privacy)}</p><small>${escapeHTML(info.scope)}</small>`;
  }catch(e){if(serial===intelAdviceSerial){intelAdviceKey='';$('advice-content').textContent=e.message;}}
};
window.loadFingerprintLab=()=>searchIntelProfiles();
async function searchIntelProfiles(){
  const serial=++intelSearchSerial;
  try{
    const rows=await api('profiles?q='+encodeURIComponent($('profile-search').value));
    if(serial!==intelSearchSerial)return;
    $('profile-count').textContent=rows.length===40?'First 40 references; refine the search.':rows.length+' fingerprint references';
    $('profile-results').innerHTML=rows.map(r=>`<button class="profile-result" data-profile="${escapeHTML(r.id)}"><strong>${escapeHTML(r.name)}</strong><small>${escapeHTML([r.vendor,r.device_type,r.source].filter(Boolean).join(' · '))} · ${r.rules} rules</small></button>`).join('')||'<p class="helper">No mapped fingerprint references found. This does not mean the device is unidentifiable.</p>';
    $('profile-results').querySelectorAll('button').forEach(button=>button.onclick=action(()=>showIntelProfile(button.dataset.profile)));
  }catch(e){if(serial===intelSearchSerial)$('profile-results').textContent=e.message;}
}
async function showIntelProfile(id){
  const serial=++intelProfileSerial;
  const info=await api('profile?id='+encodeURIComponent(id));
  if(serial!==intelProfileSerial)return;
  $('profile-detail').hidden=false;
  $('profile-detail').innerHTML=`<h3>${escapeHTML(info.name)}</h3><p class="helper">${escapeHTML(info.source)}${info.updated_at?' · source date '+escapeHTML(info.updated_at):' · source date not recorded'}. Reference data, not a detection of this computer.</p>${info.vendor?'<button id="profile-oui" class="secondary">Find this vendor’s OUIs</button>':''}<div class="reference-rules">${info.rules.map((r,i)=>`<div><code>${escapeHTML(r.signature)}</code><small>${escapeHTML(r.packet_type)} · ${escapeHTML(r.source)}</small><button class="text-button" data-reference="${i}">Look up this reference →</button></div>`).join('')}</div>`;
  if(info.vendor)$('profile-oui').onclick=()=>{$('vendor-search').value=info.vendor;view('catalog');};
  if(info.truncated)$('profile-detail').insertAdjacentHTML('beforeend','<p class="helper">Showing the first 20 of '+Number(info.total_rules)+' rules.</p>');
  $('profile-detail').querySelectorAll('[data-reference]').forEach(button=>button.onclick=action(async()=>{
    $('fingerprint-options').value=info.rules[Number(button.dataset.reference)].signature;
    intelOrigin='Corpus reference: '+info.name+' — not captured from this machine';
    await lookupFingerprint();
    $('fingerprint-result').scrollIntoView({behavior:'smooth',block:'start'});
  }));
}
async function lookupFingerprint(){
  const serial=++intelLookupSerial;
  const origin=intelOrigin;
  $('fingerprint-result').textContent='Looking up the offline corpus…';
  try{
    const result=await api('fingerprints?options='+encodeURIComponent($('fingerprint-options').value));
    if(serial!==intelLookupSerial)return;
    $('fingerprint-result').innerHTML=`<p class="eyebrow">${escapeHTML(origin)}</p><h3>${result.total_rules?result.total_rules+' matching rules':result.known_signature?'Known sequence; no device mapping':'No exact match in this snapshot'}</h3><p class="helper">${escapeHTML(result.scope)} ${escapeHTML(result.note)}</p><div class="fingerprint-matches">${result.matches.map(r=>`<article><strong>${escapeHTML(r.name)}</strong><small>${escapeHTML([r.vendor,r.device_type].filter(Boolean).join(' · '))}</small><p>${escapeHTML(r.source)} · packet: ${escapeHTML(r.packet_type)}${r.weight?' · corpus weight '+escapeHTML(r.weight)+' (not %)':''}${r.updated_at?' · '+escapeHTML(r.updated_at):''}</p>${Object.keys(r.conditions).length?'<p>Additional conditions, not checked: '+escapeHTML(JSON.stringify(r.conditions))+'</p>':''}</article>`).join('')}</div>${result.truncated?'<p class="helper">Showing the first 60 rule matches.</p>':''}`;
  }catch(e){if(serial===intelLookupSerial)$('fingerprint-result').textContent=e.message;}
}
$('guided-private').onclick=()=>$('generate').click();
$('guided-fingerprints').onclick=()=>view('fingerprints');
$('profile-search').addEventListener('input',()=>{intelSearchSerial++;clearTimeout(searchIntelProfiles.timer);searchIntelProfiles.timer=setTimeout(searchIntelProfiles,220);});
$('fingerprint-options').addEventListener('input',()=>{intelOrigin='User-entered sequence';intelLookupSerial++;});
$('fingerprint-check').onclick=action(lookupFingerprint);
$('fingerprint-options').addEventListener('keydown',e=>{if(e.key==='Enter')$('fingerprint-check').click();});
