'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="mac-session"]').content;
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state = null, selected = null, candidate = null, pending = null, firstLoad = true;
let lookupSerial = 0, searchSerial = 0, candidateSerial = 0;
async function api(path, body) {
  const options = {headers:{'X-MAC-Token':token}};
  if(body !== undefined){options.method='POST';options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  const response = await fetch('/api/'+path, options);
  const data = await response.json();
  if(!response.ok) throw Error(data.error || 'The request failed.');
  return data;
}
function toast(text) { $('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,6500); }
function action(fn){return async (...args)=>{try{await fn(...args);}catch(e){toast(e.message);}};}
function view(name){document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==name);document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('on',el.dataset.view===name));window.scrollTo(0,0);if(name==='catalog')search();}
document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>view(el.dataset.view)));
document.querySelectorAll('[data-close]').forEach(el=>el.addEventListener('click',()=>$(el.dataset.close).close()));
function current(){return state?.adapters.find(a=>a.id===selected);}
function theme(value){document.documentElement.dataset.theme=value;$('theme').textContent=value==='dark'?'Switch to light':'Switch to dark';}
function labelIntel(info){return info?.match?.vendor || (info?.local?'Local address · no vendor attribution':'No registered vendor match');}
function updateButtons(){
  const a=current(); const blocked=!a||!state?.admin||state.busy||state.refreshing||!a.registry_available||['Disabled','Not Present'].includes(a.status);
  $('apply').disabled=blocked||!candidate?.usable||candidate.mac===a?.mac;
  $('restore').disabled=blocked||!a?.override;
  $('apply-hint').textContent=!state?.admin?'Administrator mode is required to apply or restore. Open the gear to relaunch.':'Applying restarts the selected adapter and briefly disconnects it.';
}
function render(){
  const all=$('all-adapters').checked;
  const visible=state.adapters.filter(a=>all||a.physical);
  if(!visible.some(a=>a.id===selected))selected=visible[0]?.id||null;
  $('catalog-count').textContent=Number(state.catalog.records).toLocaleString();
  $('version').textContent='VERSION '+state.version;
  $('privilege').textContent=state.admin?'Administrator':'Inspection mode';
  $('refresh').disabled=state.refreshing||state.busy;
  $('refresh').textContent=state.refreshing?'Reading…':'Refresh ↻';
  $('elevate').disabled=state.admin||state.preview||state.busy;
  $('repo').disabled=state.preview; $('exit').disabled=state.preview||state.busy;
  $('adapters').innerHTML=visible.map(a=>`<button class="adapter ${a.id===selected?'selected':''}" data-id="${escapeHTML(a.id)}"><span class="adapter-line"><strong>${escapeHTML(a.name)}</strong><em>${escapeHTML(a.status)}</em></span><small>${escapeHTML(a.mac||'No MAC reported')}</small></button>`).join('')||`<p class="empty">${state.refreshing?'Reading Windows adapters…':'No physical adapters found. Include virtual adapters or refresh.'}</p>`;
  $('adapters').querySelectorAll('button').forEach(el=>el.onclick=()=>{selected=el.dataset.id;render();});
  const a=current();
  $('adapter-name').textContent=a?.name||'SELECT AN ADAPTER';
  $('adapter-status').textContent=a?(a.override?'OVERRIDE CONFIGURED':a.status.toUpperCase()):'NO SELECTION';
  $('current-mac').textContent=a?.mac||'—';
  $('vendor').textContent=a?labelIntel(a.intel):'Current address appears here';
  $('permanent').textContent=a?.permanent||'Not reported by driver';
  $('ipv4').textContent=a?.ipv4?.join(', ')||'No IPv4 assigned';
  $('address-kind').textContent=a?.intel?.kind||'—';
  $('override').textContent=a?.override||'None';
  $('adapter-description').textContent=a?[a.description,a.speed].filter(Boolean).join(' · '):'';
  $('updated').textContent=state.updated?'Observed '+new Date(state.updated).toLocaleTimeString([],{hour:'numeric',minute:'2-digit',second:'2-digit'}):'Waiting for Windows';
  $('status-text').textContent=state.busy?'Applying change · waiting for Windows verification':state.error?'Adapter status unavailable':state.refreshing?'Reading adapter state…':'Ready · changes require an explicit apply';
  const notice=state.error||(state.result?state.result.status.toUpperCase()+': '+state.result.message:'');
  $('notice').hidden=!notice; $('notice').textContent=notice;
  $('activity-list').innerHTML=[...state.events].reverse().map(e=>`<div class="event"><time>${escapeHTML(new Date(e.time).toLocaleTimeString())}</time><div>${escapeHTML(e.message)}</div></div>`).join('');
  $('source').textContent=`Source: OUI Master Database · snapshot ${state.catalog.snapshot_utc.slice(0,10)} · ${Number(state.catalog.vendors).toLocaleString()} distinct registered owner labels.`;
  updateButtons();
}
async function poll(){try{state=await api('state');if(firstLoad){theme(state.settings.theme);firstLoad=false;window.appReady=true;}render();if(!state.refreshing)api("ready",{title:document.title,ready:true,adapters:document.querySelectorAll(".adapter").length,theme:document.documentElement.dataset.theme}).catch(()=>{});}catch(e){$('status-text').textContent='App connection lost · '+e.message;}$('status-text').title=$('status-text').textContent;}
async function inspectCandidate(){const serial=++candidateSerial;candidate=null;updateButtons();const value=$('candidate').value.trim();if(!value){$('candidate-info').textContent='Generate a private address or enter your own.';return;}try{const info=await api('inspect?mac='+encodeURIComponent(value));if(serial!==candidateSerial)return;candidate=info;$('candidate-info').textContent=info.kind+' · '+(!info.usable?'Not valid for an adapter.':info.match?info.match.vendor:info.local?'Private address; no vendor identity implied.':'No registered vendor match.');}catch(e){if(serial!==candidateSerial)return;$('candidate-info').textContent=e.message;}updateButtons();}
async function generate(prefix){const info=await api('generate',prefix?{prefix}:{});$('candidate').value=info.mac;await inspectCandidate();view('workspace');}
async function search(){const serial=++searchSerial;const query=$('vendor-search').value;try{const rows=await api('search?q='+encodeURIComponent(query));if(serial!==searchSerial)return;$('search-count').textContent=rows.length===60?'Showing the first 60 matches. Refine your search.':rows.length+' matching address blocks';$('vendor-results').innerHTML=rows.map(r=>`<tr><td>${escapeHTML(r.vendor)}</td><td>${escapeHTML(r.prefix.match(/.{1,2}/g).join(':'))}</td><td>${escapeHTML(r.registry)}</td><td>${escapeHTML(r.country||'—')}</td><td><button data-prefix="${escapeHTML(r.prefix)}" ${r.status!=='current'||(parseInt(r.prefix.slice(0,2),16)&3)?'disabled':''}>Use prefix</button></td></tr>`).join('')||'<tr><td colspan="5">No matching prefixes.</td></tr>';$('vendor-results').querySelectorAll('button').forEach(el=>el.onclick=action(()=>generate(el.dataset.prefix)));}catch(e){toast(e.message);}}
$('candidate').addEventListener('input',()=>{candidateSerial++;candidate=null;updateButtons();clearTimeout(inspectCandidate.timer);inspectCandidate.timer=setTimeout(inspectCandidate,180);});
$('generate').onclick=action(()=>generate());
$('choose-vendor').onclick=()=>{view('catalog');$('vendor-search').focus();};
$('vendor-search').addEventListener('input',()=>{clearTimeout(search.timer);search.timer=setTimeout(search,180);});
$('all-adapters').onchange=render;
$('refresh').onclick=action(async()=>{await api('refresh',{});await poll();});
$('theme').onclick=action(async()=>{const next=document.documentElement.dataset.theme==='dark'?'light':'dark';await api('theme',{theme:next});theme(next);});
$('settings').onclick=()=>$('settings-dialog').showModal();
$('elevate').onclick=action(()=>api('elevate',{}));
$('repo').onclick=action(()=>api('repo',{}));
$('exit').onclick=action(()=>api('quit',{}));
$('inspect').onclick=action(async()=>{const serial=++lookupSerial;const info=await api('inspect?mac='+encodeURIComponent($('lookup-mac').value));if(serial!==lookupSerial)return;const match=info.match;$('inspection').innerHTML=`<b>${escapeHTML(info.mac)}</b> · ${escapeHTML(info.kind)}<br>${escapeHTML(match?match.vendor+' · '+match.registry+' · '+match.country:'No reliable vendor attribution')}${info.convention?'<br>Matches a '+escapeHTML(info.convention)+' address convention; this does not identify the actual runtime.':''}<br>${escapeHTML(info.note)}${match?'<br>Sources: '+escapeHTML(match.sources.join(', ')):''}`;});
$('lookup-mac').addEventListener('keydown',e=>{if(e.key==='Enter')$('inspect').click();});
$('copy').onclick=action(async()=>{if(!$('candidate').value)throw Error('Generate or enter an address first.');await navigator.clipboard.writeText($('candidate').value);toast('Address copied.');});
function confirmChange(restore){const a=current();if(!a)return;pending={id:a.id,address:restore?null:candidate?.mac,confirmed:true};$('confirm-title').textContent=restore?'Restore hardware default':'Apply address';$('confirm-text').textContent='Selected adapter: '+a.name+' · '+a.description;$('confirm-address').textContent=restore?(a.permanent||'Remove configured override'):candidate.mac;$('confirm-dialog').showModal();}
$('apply').onclick=()=>confirmChange(false);$('restore').onclick=()=>confirmChange(true);
$('confirm-change').onclick=action(async()=>{if(!pending)return;const request=pending;pending=null;$('confirm-change').disabled=true;try{await api('change',request);$('confirm-dialog').close();await poll();}finally{$('confirm-change').disabled=false;}});
$('export').onclick=action(async()=>{const report=await api('export');const blob=new Blob([JSON.stringify({product:'MAC // Spoofer',company:'Net Works Lab LLC',exported:new Date().toISOString(),...report},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='MAC-Spoofer-snapshot.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);toast('Snapshot exported.');});
poll();setInterval(poll,1800);setInterval(()=>{if(state&&!state.busy&&!state.refreshing)api('refresh',{}).catch(()=>{});},20000);
