const $=id=>document.getElementById(id);
const fa=v=>String(v??"").replace(/\d/g,d=>"۰۱۲۳۴۵۶۷۸۹"[d]);

const STATIC_SOURCES = [
  {code:"pubmed",name:"PubMed / MEDLINE",note:"نسخه کامل: اتصال از طریق FastAPI"},
  {code:"clinicaltrials",name:"ClinicalTrials.gov",note:"نسخه کامل: اتصال از طریق FastAPI"},
  {code:"openalex",name:"OpenAlex",note:"نیازمند API Key در Backend"},
  {code:"crossref",name:"Crossref",note:"نسخه کامل: اتصال از طریق FastAPI"}
];

function renderSources(){
  const box=$("sourceChecks");
  box.innerHTML="";
  for(const s of STATIC_SOURCES){
    const label=document.createElement("label");
    label.className="source-check";
    label.innerHTML=`<input type="checkbox" checked disabled>
      <span><b>${s.name}</b><small>${s.note}</small></span>`;
    box.appendChild(label);
  }
  const select=$("evidenceSource");
  select.innerHTML='<option value="all">همه منابع</option>';
  for(const s of STATIC_SOURCES) select.add(new Option(s.name,s.code));
}

function demoCards(){
  $("score").textContent="—";
  $("priority").textContent="نسخه نمایشی GitHub Pages";
  $("evidenceCount").textContent="—";
  $("maturity").textContent="—";
  $("maturityScore").textContent="Backend لازم است";
  $("ethics").textContent="—";
  $("ethicsScore").textContent="Backend لازم است";
  $("iran").textContent="—";
  $("iranScore").textContent="Backend لازم است";
  $("trend").textContent="—";
  $("trendDetail").textContent="Backend لازم است";
}

function staticNotice(){
  const warning=$("warnings");
  warning.hidden=false;
  warning.innerHTML=
   "این صفحه نسخه عمومی GitHub Pages است. رابط کاربری به‌صورت کامل نمایش داده می‌شود، اما جستجوی واقعی چندمنبعی، SQLite، تاریخچه اسکن و Export توسط FastAPI اجرا می‌شوند و روی GitHub Pages قابل اجرا نیستند. برای عملکرد کامل، پروژه را محلی یا روی یک سرویس Backend اجرا کنید.";
}

function runStatic(){
  const q=$("query").value.trim();
  const msg=q
    ? `موضوع «${q}» دریافت شد؛ اجرای واقعی این پایش به Backend نیاز دارد.`
    : "برای اجرای پایش واقعی، نسخه Backend پروژه را اجرا کنید.";
  $("evidenceList").innerHTML=`<div class="warnings">${msg}</div>`;
  staticNotice();
}

$("runBtn").onclick=runStatic;
$("evidenceSource").onchange=()=>{};
$("jsonBtn").onclick=()=>alert("Export در نسخه Full-stack فعال است.");
$("csvBtn").onclick=()=>alert("Export در نسخه Full-stack فعال است.");
$("pdfBtn").onclick=()=>alert("Export در نسخه Full-stack فعال است.");
$("refreshHistory").onclick=()=>alert("تاریخچه اسکن در SQLite نسخه Full-stack ذخیره می‌شود.");

$("fromYear").value=new Date().getFullYear()-4;
$("toYear").value=new Date().getFullYear();
$("health").textContent="● GitHub Pages";
$("health").classList.add("ok");

renderSources();
demoCards();
staticNotice();
$("historyList").innerHTML='<div class="empty">تاریخچه در نسخه Full-stack از SQLite خوانده می‌شود.</div>';
