const $=id=>document.getElementById(id);
let current=null;
let sources=[];

function fa(v){return String(v??"").replace(/\d/g,d=>"۰۱۲۳۴۵۶۷۸۹"[d])}
function esc(s=""){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}

async function api(url,opts={}){
 const r=await fetch(url,{headers:{"Content-Type":"application/json"},...opts});
 if(!r.ok){let d;try{d=await r.json()}catch{};throw new Error(d?.detail||`${r.status} ${r.statusText}`)}
 return r.json()
}

async function init(){
 try{
  const h=await api("/api/health");$("health").textContent="● سامانه آماده";$("health").classList.add("ok");
  $("toYear").value=new Date().getFullYear();$("fromYear").value=new Date().getFullYear()-4;
  sources=await api("/api/sources");renderSources();
  await loadHistory();
 }catch(e){$("health").textContent="خطا در Backend"}
}

function renderSources(){
 const box=$("sourceChecks");box.innerHTML="";
 $("evidenceSource").innerHTML='<option value="all">همه منابع</option>';
 for(const s of sources){
  const disabled=s.code==="openalex"&&!s.configured;
  const label=document.createElement("label");label.className="source-check"+(disabled?" disabled":"");
  label.innerHTML=`<input type="checkbox" value="${s.code}" ${disabled?"":"checked"} ${disabled?"disabled":""}>
   <span><b>${esc(s.name)}</b><small>${esc(s.configuration_note||"")}</small></span>`;
  box.appendChild(label);
  $("evidenceSource").add(new Option(s.name,s.code));
 }
}

function selectedSources(){
 return [...document.querySelectorAll("#sourceChecks input:checked")].map(x=>x.value)
}

async function runScan(){
 const query=$("query").value.trim();
 if(query.length<2){alert("موضوع جستجو را وارد کنید.");return}
 const active=selectedSources();
 if(!active.length){alert("حداقل یک منبع را انتخاب کنید.");return}
 const btn=$("runBtn");btn.disabled=true;btn.textContent="در حال پایش...";
 $("evidenceList").innerHTML='<div class="empty">در حال جستجو و تحلیل چندمنبعی...</div>';
 try{
  current=await api("/api/scan",{method:"POST",body:JSON.stringify({
   query,sources:active,max_results:+$("maxResults").value,
   from_year:+$("fromYear").value||null,to_year:+$("toYear").value||null,
   iran_focus:$("iranFocus").checked
  })});
  renderSignal(current.signal);renderEvidence();enableExports();await loadHistory();
 }catch(e){
  $("evidenceList").innerHTML=`<div class="warnings">${esc(e.message)}</div>`;
 }finally{btn.disabled=false;btn.textContent="اجرای پایش"}
}

function setBar(key,value){
 const v=Math.max(0,Math.min(100,+value||0));$("bar"+key).style.width=v+"%";$("bar"+key+"Text").textContent=fa(v.toFixed(1))+"/۱۰۰"
}
function renderSignal(s){
 $("score").textContent=fa(s.signal_score)+"/۱۰۰";$("priority").textContent=s.priority;
 $("evidenceCount").textContent=fa(s.evidence_count);
 $("maturity").textContent=s.maturity.stage;$("maturityScore").textContent=fa(s.maturity.score)+"/۱۰۰";
 $("ethics").textContent=s.ethics.intensity;$("ethicsScore").textContent=fa(s.ethics.score)+"/۱۰۰";
 $("iran").textContent=s.iran.level;$("iranScore").textContent=fa(s.iran.score)+"/۱۰۰";
 $("trend").textContent=s.trend.direction;$("trendDetail").textContent=`${fa(s.trend.recent_count)} اخیر / ${fa(s.trend.previous_count)} قبلی`;
 setBar("Trend",s.trend.score);setBar("Clinical",s.clinical_activity_score);setBar("Ethics",s.ethics.score);setBar("Iran",s.iran.score);setBar("Novelty",s.novelty_score);
 $("ethicsDomains").innerHTML=Object.entries(s.ethics.domains).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<span class="tag">${esc(k)}: ${fa(v)}</span>`).join("");
 $("maturityMarkers").innerHTML=(s.maturity.markers.length?s.maturity.markers:["نشانه صریحی یافت نشد"]).map(x=>`<span class="tag">${esc(x)}</span>`).join("");
 $("iranReasons").innerHTML=(s.iran.reasons.length?s.iran.reasons:["نشانه صریحی یافت نشد"]).map(x=>`<span class="tag">${esc(x)}</span>`).join("");
 $("sourceCounts").innerHTML=Object.entries(s.source_counts).map(([k,v])=>`<span class="tag">${esc(k)}: ${fa(v.toLocaleString())}</span>`).join("");
 const w=$("warnings");if(s.warnings?.length){w.hidden=false;w.innerHTML=s.warnings.map(esc).join("<br>")}else w.hidden=true;
}

function filteredEvidence(){
 if(!current)return[];
 const f=$("evidenceSource").value;
 return f==="all"?current.evidence:current.evidence.filter(x=>x.source===f)
}
function renderEvidence(){
 const rows=filteredEvidence(),box=$("evidenceList");box.innerHTML="";
 if(!rows.length){box.innerHTML='<div class="empty">شاهدی در این فیلتر وجود ندارد.</div>';return}
 for(const r of rows){
  const el=document.createElement("article");el.className="evidence";
  el.innerHTML=`<div class="evidence-top"><span class="badge">${esc(r.source)}</span><time>${fa(r.publication_date||r.year||"")}</time></div>
  <h3>${esc(r.title)}</h3>
  <div class="meta">${esc([r.authors?.slice(0,4).join(", "),r.doi||r.external_id].filter(Boolean).join(" · "))}</div>
  <p class="abstract">${esc(r.abstract||"No abstract/summary available.")}</p>
  <div class="evidence-actions">${r.url?`<a href="${esc(r.url)}" target="_blank" rel="noreferrer">مشاهده منبع ↗</a>`:""}<button>نمایش کامل</button></div>`;
  el.querySelector("button").onclick=()=>{el.classList.toggle("open");el.querySelector("button").textContent=el.classList.contains("open")?"بستن":"نمایش کامل"};
  box.appendChild(el)
 }
}
function enableExports(){
 for(const id of ["jsonBtn","csvBtn","pdfBtn"])$(id).disabled=false
}
function download(ext){if(current)location.href=`/api/export/${current.scan_id}.${ext}`}
async function loadHistory(){
 const rows=await api("/api/scans?limit=30"),box=$("historyList");box.innerHTML="";
 if(!rows.length){box.innerHTML='<div class="empty">هنوز اسکن ذخیره‌شده‌ای وجود ندارد.</div>';return}
 for(const r of rows){
  const el=document.createElement("div");el.className="history-item";
  el.innerHTML=`<strong>${esc(r.query)}</strong><span>${esc(r.status)}</span><span>${r.signal_score==null?"—":fa(r.signal_score)+"/۱۰۰"}</span><button>باز کردن</button>`;
  el.querySelector("button").onclick=()=>openScan(r.id);box.appendChild(el)
 }
}
async function openScan(id){
 const d=await api(`/api/scans/${id}`);
 current={scan_id:id,query:d.scan.query,signal:d.signal,evidence:d.evidence.map(x=>({
  source:x.source_code,external_id:x.external_id,evidence_type:x.evidence_type,title:x.title,abstract:x.abstract,
  publication_date:x.publication_date,year:x.year,url:x.url,doi:x.doi,authors:x.authors,affiliations:x.affiliations,metadata:x.metadata
 }))};
 $("query").value=d.scan.query;renderSignal(d.signal);renderEvidence();enableExports();location.hash="#overview";
}

$("runBtn").onclick=runScan;$("evidenceSource").onchange=renderEvidence;
$("jsonBtn").onclick=()=>download("json");$("csvBtn").onclick=()=>download("csv");$("pdfBtn").onclick=()=>download("pdf");
$("refreshHistory").onclick=loadHistory;
init();
