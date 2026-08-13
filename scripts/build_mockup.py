# -*- coding: utf-8 -*-
"""
대시보드 기획안.html 생성 스크립트.
scratch_world_inner.svg(세계지도 path, CC BY-SA 3.0), scratch_rows2.json(전 페이지 공통 필터용
로우 데이터: 고객사/공장/카테고리/월/금액/결함/국가/상태/심각도/리드타임/사이클타임)을 읽어
최종 HTML 파일을 조립한다. 페이지1(Executive Summary)·페이지3(리드타임/효율)도 더 이상
사전 집계된 정적 값을 쓰지 않고, 공통 필터 상태에 따라 로우 데이터에서 매번 재계산한다.
"""
import json

with open("scratch_world_inner.svg", encoding="utf-8") as f:
    WORLDMAP_SVG = f.read()
with open("scratch_rows2.json", encoding="utf-8") as f:
    ROWS_JSON = f.read()
with open("scratch_logo_b64.txt", encoding="ascii") as f:
    LOGO_B64 = f.read().strip()

TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>SL Corporation 품질 클레임 대시보드 — 기획안(Mockup)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{
    --navy:#16324f; --navy-2:#1f4e79; --bg:#f2f4f7; --card:#ffffff;
    --border:#e2e6ec; --text:#1c2430; --muted:#7c8494;
    --bad:#c0392b; --bad-bg:#fbeaea; --good:#1f7a4c; --good-bg:#eaf6ef;
    --amber:#d98c1f; --gray-bar:#c8d3e0;
  }
  *{box-sizing:border-box;}
  body{margin:0;font-family:"Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",sans-serif;background:var(--bg);color:var(--text);}
  .app{display:flex;align-items:flex-start;min-height:100vh;}

  /* Sidebar */
  .sidebar{width:220px;flex:0 0 220px;background:#ffffff;border-right:1px solid var(--border);padding:20px 0 14px;
    position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;}
  .brand-row{padding:14px 20px 0;}
  .brand-logo{height:34px;width:auto;display:block;}
  .brand-corp{padding:0 20px;font-size:11px;color:var(--muted);margin-top:5px;}
  .brand-tagline{padding:0 20px;font-size:10.5px;color:var(--navy-2);font-weight:700;margin:4px 0 18px;}
  nav{display:flex;flex-direction:column;gap:2px;}
  .nav-item{border:none;background:none;text-align:left;padding:12px 20px;font-size:13.5px;color:var(--text);cursor:pointer;border-left:3px solid transparent;}
  .nav-item:hover{background:#f5f7fa;}
  .nav-item.active{background:var(--navy);color:#fff;border-left:3px solid var(--amber);font-weight:600;}
  .sidebar-mini-foot{padding:10px 20px 0;font-size:10px;color:#b7bec8;}

  /* Main */
  main{flex:1;padding:26px 30px;min-width:0;}
  .page{display:none;}
  .page.active{display:block;}
  .page-head{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:16px;}
  .page-head h1{font-size:22px;margin:0;color:var(--navy);}
  .page-head .desc{font-size:12.5px;color:var(--muted);margin-top:4px;}
  .meta{display:flex;gap:24px;}
  .meta div{text-align:right;}
  .meta-label{display:block;font-size:10.5px;color:var(--muted);}
  .meta-value{display:block;font-size:13px;font-weight:600;}

  .card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 18px;box-shadow:0 1px 3px rgba(20,30,50,0.04);}
  .card h2{font-size:14px;margin:0 0 4px;color:var(--navy);}
  .card-sub{font-size:11px;color:var(--muted);font-weight:400;}
  .card-cap{font-size:10.5px;color:var(--muted);margin-top:8px;}

  /* KPI row */
  .kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px;}
  .kpi-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px;}
  .kpi-card.hl{background:var(--navy);color:#fff;border-color:var(--navy);}
  .kpi-label{font-size:12px;font-weight:700;}
  .kpi-card.hl .kpi-sub{color:#c3d2e2;}
  .kpi-sub{font-size:10.5px;color:var(--muted);margin-bottom:8px;}
  .kpi-main{font-size:22px;font-weight:800;margin-top:2px;}
  .kpi-unit{font-size:12px;font-weight:400;margin-left:2px;color:var(--muted);}
  .kpi-card.hl .kpi-unit{color:#c3d2e2;}
  .kpi-amount{font-size:14px;font-weight:700;margin-top:8px;color:var(--navy-2);}
  .kpi-card.hl .kpi-amount{color:#fff;}
  .kpi-change{margin-top:2px;}

  .badge{display:inline-block;font-size:10.5px;font-weight:700;padding:1px 6px;border-radius:4px;}
  .badge.bad{color:var(--bad);background:var(--bad-bg);}
  .badge.good{color:var(--good);background:var(--good-bg);}
  .badge.flat{color:var(--muted);background:#eef0f3;}
  .kpi-card.hl .badge.bad{background:#5b2a26;color:#ff8f82;}
  .kpi-card.hl .badge.good{background:#1d4a37;color:#7fe0b0;}

  /* Grids */
  .row-2{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-top:16px;}
  .row-2-b{display:grid;grid-template-columns:1.35fr 1fr;gap:16px;margin-top:16px;}
  .row-2-eq{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;}
  .stack{display:flex;flex-direction:column;gap:16px;}
  .full{margin-top:16px;}

  svg{max-width:100%;height:auto;display:block;}
  .legend{display:flex;gap:16px;margin-top:8px;font-size:11px;color:var(--muted);}
  .legend .dot{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px;vertical-align:middle;}

  /* Rank bars */
  .rank-row{display:grid;grid-template-columns:130px 1fr 78px;align-items:center;gap:8px;padding:5px 4px;font-size:11.5px;border-radius:6px;margin:0 -4px;}
  .rank-label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .rank-bar-wrap{background:#eef1f5;border-radius:4px;height:10px;overflow:hidden;}
  .rank-bar{background:var(--navy-2);height:100%;border-radius:4px;}
  .rank-val{text-align:right;font-weight:600;font-variant-numeric:tabular-nums;}
  .rank-row.clickable{cursor:pointer;transition:background .12s;}
  .rank-row.clickable:hover{background:#f2f5f9;}
  .rank-row.active{background:#e7edf5;}
  .rank-row.active .rank-bar{background:var(--amber);}
  .empty-note{font-size:12px;color:var(--muted);padding:10px 4px;}

  /* Map */
  .map-card svg.worldmap{width:100%;height:auto;display:block;background:#eef2f6;border-radius:8px;border:1px solid var(--border);}
  .worldmap path{fill:#dbe2ea;stroke:#fff;stroke-width:.6;}
  .bubble-circle{stroke:#fff;stroke-width:1.3;cursor:pointer;}
  .bubble-label{fill:#fff;font-size:9px;font-weight:700;pointer-events:none;text-anchor:middle;}
  .map-legend{display:flex;gap:18px;font-size:11px;color:var(--muted);margin-top:10px;}
  .map-insight{font-size:12px;margin-top:6px;line-height:1.6;}
  .tooltip{position:fixed;pointer-events:none;background:var(--navy);color:#fff;font-size:11.5px;line-height:1.55;
    padding:8px 10px;border-radius:6px;box-shadow:0 4px 14px rgba(0,0,0,.28);z-index:80;opacity:0;transition:opacity .1s;max-width:220px;}
  .tooltip.show{opacity:1;}

  /* small multiples */
  .small-multiples{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;}
  .sm-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 14px;cursor:pointer;transition:box-shadow .12s,border-color .12s;}
  .sm-card:hover{box-shadow:0 2px 8px rgba(20,30,50,.08);}
  .sm-card.active{border-color:var(--navy-2);box-shadow:0 0 0 2px rgba(31,78,121,.15);}
  .sm-title{font-size:12px;font-weight:700;color:var(--navy);margin-bottom:4px;}
  .sm-spark{height:44px;margin:4px 0;}
  .sm-foot{display:flex;justify-content:space-between;align-items:center;font-size:12px;}
  .sm-amt{font-weight:700;}
  .sm-cap{font-size:9.5px;color:var(--muted);margin-top:4px;}

  /* Filter bar (common — repeated identically at the top of every page) */
  .filter-bar{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;background:#fff;border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin-bottom:18px;}
  .filter-field{display:flex;flex-direction:column;gap:3px;}
  .filter-field label{font-size:10px;color:var(--muted);font-weight:700;}
  .filter-field select{font-size:12px;padding:6px 8px;border:1px solid var(--border);border-radius:6px;background:#fff;color:var(--text);min-width:150px;}
  .filter-reset{font-size:11.5px;color:var(--navy-2);background:#eef2f7;border:1px solid var(--border);border-radius:6px;padding:0 12px;height:31px;cursor:pointer;}
  .filter-reset:hover{background:#e2e8f0;}
  .filter-readout{margin-left:auto;font-size:12px;color:var(--navy);font-weight:700;background:#eef2f7;padding:7px 12px;border-radius:6px;white-space:nowrap;}

  /* Heatmap */
  .heatmap-scroll{overflow-x:auto;}
  table.heatmap{border-collapse:collapse;font-size:10.5px;width:100%;}
  table.heatmap th, table.heatmap td{padding:5px 6px;text-align:center;border:1px solid #fff;white-space:nowrap;}
  table.heatmap thead th{background:var(--navy);color:#fff;font-weight:600;height:88px;vertical-align:bottom;}
  table.heatmap thead th span{writing-mode:vertical-rl;transform:rotate(180deg);display:inline-block;}
  table.heatmap th.row-h{background:#f5f7fa;text-align:left;font-weight:600;color:var(--text);position:sticky;left:0;}

  /* status bar */
  .status-bar{display:flex;height:26px;border-radius:6px;overflow:hidden;background:#eef1f5;}
  .status-bar .seg{height:100%;}
  .status-legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;font-size:11.5px;}
  .status-legend .legend-item{display:flex;align-items:center;}
  .status-legend .dot{width:9px;height:9px;border-radius:2px;margin-right:5px;}
  .callout{margin-top:14px;padding:12px 14px;background:#fff6ea;border:1px solid #f1d9ad;border-radius:8px;font-size:12.5px;}
  .callout b{color:var(--amber);}

  /* severity */
  .sev-row{margin-bottom:12px;}
  .sev-label{font-size:12px;font-weight:700;display:flex;align-items:center;margin-bottom:3px;}
  .sev-label .dot{width:9px;height:9px;border-radius:2px;margin-right:6px;}
  .sev-stats{font-size:11px;color:var(--muted);margin-bottom:4px;}
  .sev-bar-wrap{background:#eef1f5;border-radius:4px;height:9px;overflow:hidden;}
  .sev-bar{height:100%;}

  .hist-caption{font-size:11.5px;color:var(--muted);margin-top:6px;}
  .wireframe-tag{display:inline-block;font-size:10px;font-weight:700;color:#fff;background:var(--amber);padding:2px 8px;border-radius:10px;margin-left:8px;vertical-align:middle;}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand-row">
      <img class="brand-logo" src="data:image/png;base64,__LOGO_B64__" alt="SL Corporation">
    </div>
    <div class="brand-corp">Corporation</div>
    <div class="brand-tagline">Quality Claims Dashboard</div>
    <nav>
      <button class="nav-item active" data-page="page1">1. 종합 요약</button>
      <button class="nav-item" data-page="page2">2. 원인 드릴다운</button>
      <button class="nav-item" data-page="page3">3. 리드타임·효율</button>
    </nav>
    <div class="sidebar-mini-foot">Mockup v0.3 · Synthetic Data</div>
  </aside>

  <main>
    <!-- PAGE 1 -->
    <section id="page1" class="page active">
      <div class="page-head">
        <h1>종합 요약</h1>
        <div class="meta">
          <div><span class="meta-label">기준일</span><span class="meta-value">2025.12.31</span></div>
        </div>
      </div>

      __FILTER_BAR__

      <div class="kpi-row" id="kpiRow"></div>

      <div class="card full">
        <h2>월별 클레임 건수·금액 추이 <span class="card-sub">(발생일자 기준 · 상단 필터 반영)</span></h2>
        <svg id="trendChart" viewBox="0 0 1120 300"></svg>
        <div class="legend">
          <span><span class="dot" style="background:var(--gray-bar)"></span>월별 클레임 건수 (막대·좌축)</span>
          <span><span class="dot" style="background:var(--navy)"></span>월별 클레임 금액 (라인·우축)</span>
        </div>
      </div>

      <div class="row-2">
        <div class="card map-card">
          <h2>국가별 클레임 규모 <span class="card-sub">(claim_country 기준 · 버블 크기=금액 · 마우스 오버 시 상세)</span></h2>
          <svg class="worldmap" id="worldSvg" viewBox="30.767 241.591 784.077 458.627">
__WORLDMAP__
            <g id="bubbleLayer"></g>
          </svg>
          <div class="map-legend">
            <span><span class="dot" style="background:var(--navy-2);border-radius:50%;"></span>평균 처리기간 이하 (정상)</span>
            <span><span class="dot" style="background:var(--bad);border-radius:50%;"></span>평균 처리기간 초과 (지연)</span>
          </div>
          <div class="map-insight" id="mapInsight1"></div>
          <div class="map-insight" id="mapInsight2"></div>
          <div class="card-cap">지도 출처: Simple World Map by Al MacDonald, ed. Fritz Lekschas (CC BY-SA 3.0)</div>
        </div>
        <div class="stack">
          <div class="card">
            <h2>Top 5 고객사 <span class="card-sub">(클레임 금액 기준)</span></h2>
            <div id="rankCustomer"></div>
          </div>
          <div class="card">
            <h2>Top 5 결함유형 <span class="card-sub">(클레임 금액 기준)</span></h2>
            <div id="rankDefect"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- PAGE 2 -->
    <section id="page2" class="page">
      <div class="page-head">
        <h1>원인 드릴다운</h1>
        <div class="meta">
          <div><span class="meta-label">기준일</span><span class="meta-value">2025.12.31</span></div>
        </div>
      </div>

      __FILTER_BAR__

      <h2 style="font-size:13px;color:var(--navy);margin:0 0 10px;">부품 카테고리별 클레임 금액 추이 <span class="card-sub">(클릭 시 해당 카테고리로 필터링)</span></h2>
      <div class="small-multiples" id="smallMultiples"></div>

      <div class="row-2-b">
        <div class="card">
          <h2>생산공장 × 결함유형 매트릭스 <span class="card-sub">(클레임 건수)</span></h2>
          <div class="heatmap-scroll">
            <table class="heatmap" id="heatmapTable"></table>
          </div>
          <div class="card-cap">※ 색이 진할수록 해당 공장·결함유형 조합의 클레임 건수가 많습니다.</div>
        </div>
        <div class="stack">
          <div class="card">
            <h2>부품 카테고리 랭킹 <span class="card-sub">(클레임 금액 · 클릭 시 필터링)</span></h2>
            <div id="rankCategory"></div>
          </div>
          <div class="card">
            <h2>결함유형 Top 10 <span class="card-sub">(클레임 건수 기준)</span></h2>
            <div id="rankDefectCount"></div>
          </div>
        </div>
      </div>

      <div class="card full">
        <h2>고객사별 클레임 금액 구성 <span class="card-sub">(클릭 시 해당 고객사로 필터링)</span></h2>
        <div id="custComposition"></div>
      </div>
    </section>

    <!-- PAGE 3 -->
    <section id="page3" class="page">
      <div class="page-head">
        <h1>리드타임·처리 효율</h1>
        <div class="meta">
          <div><span class="meta-label">기준일</span><span class="meta-value">2025.12.31</span></div>
        </div>
      </div>

      __FILTER_BAR__

      <div class="row-2-eq">
        <div class="card">
          <h2>클레임 상태 현황</h2>
          <div class="status-bar" id="statusBar"></div>
          <div class="status-legend" id="statusLegend"></div>
          <div class="callout" id="openCallout"></div>
        </div>
        <div class="card">
          <h2>심각도(Severity)별 분포 <span class="card-sub">(건수 · 금액 비중)</span></h2>
          <div id="severityBlock"></div>
        </div>
      </div>

      <div class="row-2-eq">
        <div class="card">
          <h2>리드타임 분포 — 발생 → 접수 <span class="card-sub">(lead_time_to_receive, 일)</span></h2>
          <svg id="histReceive" viewBox="0 0 460 220"></svg>
          <div class="hist-caption" id="histReceiveCap"></div>
        </div>
        <div class="card">
          <h2>리드타임 분포 — 접수 → 확정 <span class="card-sub">(lead_time_to_confirm, 일)</span></h2>
          <svg id="histConfirm" viewBox="0 0 460 220"></svg>
          <div class="hist-caption" id="histConfirmCap"></div>
        </div>
      </div>

      <div class="row-2-eq">
        <div class="card">
          <h2>고객사별 평균 처리기간 <span class="card-sub">(발생→확정, 일)</span></h2>
          <div id="custCycle"></div>
        </div>
        <div class="card">
          <h2>생산공장별 평균 처리기간 <span class="card-sub">(발생→확정, 일)</span></h2>
          <div id="plantCycle"></div>
        </div>
      </div>
    </section>
  </main>
</div>
<div id="mapTooltip" class="tooltip"></div>

<script>
const ROWS_DATA = __ROWS_JSON__;
const ROWS = ROWS_DATA.rows;
/* row index: 0 customer, 1 plant, 2 category, 3 ym, 4 amount, 5 defect, 6 country,
   7 status, 8 severity, 9 lead_to_receive, 10 lead_to_confirm(or null), 11 cycle_time(or null) */
const ALL_MONTHS = ROWS_DATA.months;
const ALL_CUSTOMERS = ROWS_DATA.customers;
const ALL_PLANTS = ROWS_DATA.plants;
const ALL_DEFECTS = ROWS_DATA.defects;
const ALL_CATEGORIES = ROWS_DATA.categories;
const CAT_KOR = {'Lamp Systems':'램프 시스템','Mirror Systems':'미러 시스템','Chassis Systems':'샤시 시스템','Front End Module':'프론트엔드모듈','Electrification':'전장/전동화'};
const COUNTRY_CENTROID = {US:[193.3,419.0], KR:[698.2,417.4], CN:[635.1,415.6], DE:[429.8,392.7], BR:[275.0,569.3], MX:[166.7,462.1], IN:[601.9,472.6], JP:[723.1,403.7]};
const COUNTRY_NAME = {KR:'대한민국',US:'미국',CN:'중국',DE:'독일',BR:'브라질',MX:'멕시코',IN:'인도',JP:'일본'};
const STATUS_ORDER = ['접수','조사중','확정','기각','보상완료'];
const STATUS_COLOR = {'접수':'#d98c1f','조사중':'#e2a53a','확정':'#1f4e79','기각':'#9aa4b2','보상완료':'#2a7f62'};
const SEV_ORDER = ['Critical','Major','Minor'];
const SEV_COLOR = {'Critical':'#c0392b','Major':'#d98c1f','Minor':'#7a8699'};
const RECEIVE_EDGES = [0,3,6,9,12,15,20];
const CONFIRM_EDGES = [0,5,10,15,20,25,30,35,40,45,50];

function fmtUSD(n){
  const sign = n<0?'-':'';
  n=Math.abs(n);
  if(n>=1e6) return sign+'$'+(n/1e6).toFixed(2)+'M';
  if(n>=1e3) return sign+'$'+(n/1e3).toFixed(1)+'K';
  return sign+'$'+n.toFixed(0);
}
function fmtCount(n){ return n.toLocaleString()+'건'; }
function fmtDays(n){ return n+'일'; }
function round1(n){ return Math.round(n*10)/10; }
function maxOf(arr){ return Math.max.apply(null, arr.concat([1])); }
function pctBadge(n){
  if(n===null||n===undefined||!isFinite(n)) return '<span class="badge flat">—</span>';
  const up = n>=0;
  const cls = up? 'bad':'good';
  const arrow = up? '▲':'▼';
  return '<span class="badge '+cls+'">'+arrow+' '+Math.abs(n).toFixed(1)+'%</span>';
}
function pctChange(cur,prev){ if(!prev) return null; return (cur-prev)/prev*100; }

/* ---------- Nav ---------- */
document.querySelectorAll('.nav-item').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.nav-item').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.page).classList.add('active');
  });
});

/* ---------- Generic rank bars (used across all 3 pages) ---------- */
function drawRankBars(id, items, opts){
  opts = opts || {};
  const fmt = opts.fmt || fmtUSD;
  if(!items.length){
    document.getElementById(id).innerHTML = '<div class="empty-note">해당 조건의 데이터가 없습니다.</div>';
    return;
  }
  const sorted = items.slice().sort((a,b)=>b.value-a.value).slice(0, opts.topN || items.length);
  const max = maxOf(sorted.map(e=>e.value));
  let html='';
  sorted.forEach((e,i)=>{
    const w = (max>0 ? e.value/max*100 : 0).toFixed(1);
    const clickable = opts.clickField ? ' clickable' : '';
    const active = (opts.clickField && filters[opts.clickField]===e.key) ? ' active' : '';
    html += '<div class="rank-row'+clickable+active+'" data-key="'+String(e.key).replace(/"/g,'&quot;')+'">'
      +'<div class="rank-label">'+(i+1)+'. '+e.label+'</div>'
      +'<div class="rank-bar-wrap"><div class="rank-bar" style="width:'+w+'%"></div></div>'
      +'<div class="rank-val">'+fmt(e.value)+'</div></div>';
  });
  document.getElementById(id).innerHTML = html;
  if(opts.clickField){
    document.querySelectorAll('#'+id+' .rank-row').forEach(el=>{
      el.addEventListener('click', ()=>{
        const key = el.dataset.key;
        filters[opts.clickField] = (filters[opts.clickField]===key) ? '전체' : key;
        syncFilterUI();
        rebuildAll();
      });
    });
  }
}

/* ================= Common filters (shared across all 3 pages) ================= */
const filters = {customer:'전체', plant:'전체', category:'전체', period:'all'};

function populateFilters(){
  document.querySelectorAll('.f-customer').forEach(sel=>{
    ALL_CUSTOMERS.forEach(c=>{ const o=document.createElement('option'); o.value=c; o.textContent=c; sel.appendChild(o); });
  });
  document.querySelectorAll('.f-plant').forEach(sel=>{
    ALL_PLANTS.forEach(p=>{ const o=document.createElement('option'); o.value=p; o.textContent=p; sel.appendChild(o); });
  });
  document.querySelectorAll('.f-category').forEach(sel=>{
    ALL_CATEGORIES.forEach(c=>{ const o=document.createElement('option'); o.value=c; o.textContent=CAT_KOR[c]||c; sel.appendChild(o); });
  });
}

function syncFilterUI(){
  document.querySelectorAll('.f-customer').forEach(el=>{ el.value = filters.customer; });
  document.querySelectorAll('.f-plant').forEach(el=>{ el.value = filters.plant; });
  document.querySelectorAll('.f-category').forEach(el=>{ el.value = filters.category; });
  document.querySelectorAll('.f-period').forEach(el=>{ el.value = filters.period; });
}

function periodMinYm(period){
  if(period==='all') return ALL_MONTHS[0];
  const n = period==='12m'?12: period==='6m'?6:3;
  const idx = Math.max(0, ALL_MONTHS.length-n);
  return ALL_MONTHS[idx];
}

/* customer/plant/category always apply; period optionally ignored (KPI cards define their own windows) */
function filteredRows(ignorePeriod){
  const minYm = ignorePeriod ? null : periodMinYm(filters.period);
  return ROWS.filter(r=>
    (filters.customer==='전체' || r[0]===filters.customer) &&
    (filters.plant==='전체' || r[1]===filters.plant) &&
    (filters.category==='전체' || r[2]===filters.category) &&
    (ignorePeriod || r[3] >= minYm)
  );
}

['customer','plant','category','period'].forEach(key=>{
  const cls = '.f-'+key;
  document.querySelectorAll(cls).forEach(el=>{
    el.addEventListener('change', e=>{
      filters[key] = e.target.value;
      syncFilterUI();
      rebuildAll();
    });
  });
});
document.querySelectorAll('.filter-reset').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    filters.customer='전체'; filters.plant='전체'; filters.category='전체'; filters.period='all';
    syncFilterUI();
    rebuildAll();
  });
});

function updateReadouts(rows){
  const amt = rows.reduce((s,r)=>s+r[4],0);
  const text = '필터 결과: '+rows.length.toLocaleString()+'건 · '+fmtUSD(amt);
  document.querySelectorAll('.filter-readout').forEach(el=>{ el.textContent = text; });
}

/* ================= Page 1 : Executive Summary ================= */
function computeKpiWindows(rowsNoPeriod){
  function stat(minYm,maxYm){
    const sub = rowsNoPeriod.filter(r=> r[3]>=minYm && r[3]<=maxYm);
    return {count: sub.length, amount: sub.reduce((s,r)=>s+r[4],0)};
  }
  return {
    last1m: stat('2025-12','2025-12'), last1m_prev: stat('2024-12','2024-12'),
    last3m: stat('2025-10','2025-12'), last3m_prev: stat('2024-10','2024-12'),
    last6m: stat('2025-07','2025-12'), last6m_prev: stat('2024-07','2024-12'),
    last12m: stat('2025-01','2025-12'), last12m_prev: stat('2024-01','2024-12'),
    all: stat('2023-01','2025-12'),
  };
}

function drawKPIRow(rowsNoPeriod){
  const k = computeKpiWindows(rowsNoPeriod);
  const defs = [
    {label:'최근 1개월', sub:'2025.12', cur:k.last1m, prev:k.last1m_prev},
    {label:'최근 3개월', sub:'2025.10~12', cur:k.last3m, prev:k.last3m_prev},
    {label:'최근 6개월', sub:'2025.07~12', cur:k.last6m, prev:k.last6m_prev},
    {label:'최근 12개월', sub:'2025.01~12', cur:k.last12m, prev:k.last12m_prev},
    {label:'전체(3개년)', sub:'2023.01~2025.12', cur:k.all, prev:null, hl:true},
  ];
  let html='';
  defs.forEach(d=>{
    const countPct = pctChange(d.cur.count, d.prev? d.prev.count:null);
    const amtPct = pctChange(d.cur.amount, d.prev? d.prev.amount:null);
    html += '<div class="kpi-card '+(d.hl?'hl':'')+'">'
      +'<div class="kpi-label">'+d.label+'</div>'
      +'<div class="kpi-sub">'+d.sub+(d.prev?' · 전년동기比':'')+' · 기간 필터 미적용</div>'
      +'<div class="kpi-main">'+d.cur.count.toLocaleString()+'<span class="kpi-unit">건</span></div>'
      +'<div class="kpi-change">'+pctBadge(countPct)+'</div>'
      +'<div class="kpi-amount">'+fmtUSD(d.cur.amount)+'</div>'
      +'<div class="kpi-change">'+pctBadge(amtPct)+'</div>'
      +'</div>';
  });
  document.getElementById('kpiRow').innerHTML = html;
}

function drawTrendChart(rows){
  const months = ALL_MONTHS.filter(m=>m>=periodMinYm(filters.period));
  const byMonth = {}; months.forEach(m=>{ byMonth[m]={count:0,amount:0}; });
  rows.forEach(r=>{ const b=byMonth[r[3]]; if(b){ b.count++; b.amount+=r[4]; } });
  const data = months.map(m=>({ym:m, count:byMonth[m].count, amount:byMonth[m].amount}));

  const W=1120,H=300,padL=46,padR=54,padT=26,padB=40;
  const innerW=W-padL-padR, innerH=H-padT-padB;
  const maxCount = maxOf(data.map(d=>d.count));
  const maxAmt = maxOf(data.map(d=>d.amount));
  const n=Math.max(1,data.length);
  const bw = innerW/n*0.6;
  const xFor=(i)=> padL + innerW*(i+0.5)/n;
  const yCount=(v)=> padT+innerH - innerH*(v/maxCount)*0.92;
  const yAmt=(v)=> padT+innerH - innerH*(v/maxAmt)*0.92;

  let bars='';
  data.forEach((d,i)=>{
    const x=xFor(i)-bw/2, y=yCount(d.count);
    bars+='<rect x="'+x+'" y="'+y+'" width="'+bw+'" height="'+(padT+innerH-y)+'" fill="#c8d3e0" rx="1"></rect>';
  });
  const pathPts = data.map((d,i)=>xFor(i)+','+yAmt(d.amount)).join(' ');
  let dots='';
  data.forEach((d,i)=>{ dots+='<circle cx="'+xFor(i)+'" cy="'+yAmt(d.amount)+'" r="2.2" fill="#16324f"></circle>'; });

  let yearLines='', xLabels='';
  data.forEach((d,i)=>{
    if(d.ym.endsWith('-01')){
      const x = xFor(i)-bw/2-4;
      yearLines+='<line x1="'+x+'" y1="'+padT+'" x2="'+x+'" y2="'+(padT+innerH)+'" stroke="#e5e7eb" stroke-dasharray="3,3"></line>';
      yearLines+='<text x="'+(x+4)+'" y="16" font-size="11" fill="#8a93a3">'+d.ym.slice(0,4)+'</text>';
    }
    if(i%3===0){
      xLabels+='<text x="'+xFor(i)+'" y="'+(H-14)+'" font-size="10" fill="#8a93a3" text-anchor="middle">'+d.ym.slice(5,7)+'월</text>';
    }
  });
  const axisCap = '<text x="'+padL+'" y="16" font-size="10" fill="#8a93a3">건수 최대 '+maxCount+'건</text>'
    + '<text x="'+(W-padR)+'" y="16" font-size="10" fill="#8a93a3" text-anchor="end">금액 최대 '+fmtUSD(maxAmt)+'</text>';

  document.getElementById('trendChart').innerHTML = data.length
    ? (yearLines+bars+'<polyline points="'+pathPts+'" fill="none" stroke="#16324f" stroke-width="2.4"></polyline>'+dots+xLabels+axisCap)
    : '<text x="20" y="30" font-size="12" fill="#8a93a3">해당 조건의 데이터가 없습니다.</text>';
}

function computeCountryStats(rows){
  const g = {};
  rows.forEach(r=>{
    const c = r[6];
    if(!g[c]) g[c] = {country:c, count:0, amount:0, cycleSum:0, cycleN:0};
    g[c].count++; g[c].amount += r[4];
    if(r[11]!==null){ g[c].cycleSum += r[11]; g[c].cycleN++; }
  });
  return Object.keys(g).map(c=>({
    country:c, count:g[c].count, amount: round1(g[c].amount),
    avg_cycle: g[c].cycleN ? round1(g[c].cycleSum/g[c].cycleN) : null,
  }));
}

function drawBubbleMap(rows){
  Object.keys(COUNTRY_CENTROID).forEach(cc=>{
    const el = document.getElementById(cc.toLowerCase());
    if(el){ el.style.fill = ''; }
  });
  const countries = computeCountryStats(rows).filter(c=>c.avg_cycle!==null);
  const layer = document.getElementById('bubbleLayer');
  if(!countries.length){
    layer.innerHTML = '';
    document.getElementById('mapInsight1').textContent = '해당 조건에 부합하는 클레임이 없습니다.';
    document.getElementById('mapInsight2').textContent = '';
    return;
  }
  const maxAmt = maxOf(countries.map(c=>c.amount));
  const minAmt = Math.min.apply(null, countries.map(c=>c.amount));
  const rScale = v => 9 + 24*Math.sqrt(maxAmt>minAmt ? (v-minAmt)/(maxAmt-minAmt) : 1);
  const avgCycle = countries.reduce((s,c)=>s+c.avg_cycle,0)/countries.length;
  let inner='';
  countries.forEach(c=>{
    const p = COUNTRY_CENTROID[c.country];
    if(!p) return;
    const r = rScale(c.amount);
    const over = c.avg_cycle>avgCycle;
    const fill = over? '#c0392b':'#1f4e79';
    const el = document.getElementById(c.country.toLowerCase());
    if(el){ el.style.fill = over? 'rgba(192,57,43,.55)':'rgba(31,78,121,.55)'; }
    inner += '<circle class="bubble-circle" cx="'+p[0]+'" cy="'+p[1]+'" r="'+r+'" fill="'+fill+'" data-country="'+c.country+'" data-name="'+COUNTRY_NAME[c.country]+'" data-amount="'+c.amount+'" data-count="'+c.count+'" data-cycle="'+c.avg_cycle+'"></circle>';
    inner += '<text class="bubble-label" x="'+p[0]+'" y="'+(p[1]+3)+'">'+c.country+'</text>';
  });
  layer.innerHTML = inner;

  const tip = document.getElementById('mapTooltip');
  layer.querySelectorAll('.bubble-circle').forEach(el=>{
    el.addEventListener('mousemove', (e)=>{
      const d = el.dataset;
      tip.innerHTML = '<b>'+d.name+'</b><br>클레임 금액: '+fmtUSD(+d.amount)+'<br>클레임 건수: '+Number(d.count).toLocaleString()+'건<br>평균 처리기간: '+d.cycle+'일';
      tip.style.left = (e.clientX+14)+'px';
      tip.style.top = (e.clientY+14)+'px';
      tip.classList.add('show');
    });
    el.addEventListener('mouseleave', ()=>{ tip.classList.remove('show'); });
  });

  const byAmt=countries.slice().sort((a,b)=>b.amount-a.amount);
  const byCycle=countries.slice().sort((a,b)=>b.avg_cycle-a.avg_cycle);
  document.getElementById('mapInsight1').innerHTML = '클레임 금액이 가장 큰 국가는 <b>'+COUNTRY_NAME[byAmt[0].country]+'</b> ('+fmtUSD(byAmt[0].amount)+', '+byAmt[0].count+'건) 입니다.';
  document.getElementById('mapInsight2').innerHTML = '평균 처리기간이 가장 긴 국가는 <b>'+COUNTRY_NAME[byCycle[0].country]+'</b> (평균 '+byCycle[0].avg_cycle+'일) 입니다.';
}

function rebuildPage1(rowsNoPeriod, rowsWithPeriod){
  drawKPIRow(rowsNoPeriod);
  drawTrendChart(rowsWithPeriod);
  drawBubbleMap(rowsWithPeriod);

  const custSums = {}; rowsWithPeriod.forEach(r=>{ custSums[r[0]] = (custSums[r[0]]||0)+r[4]; });
  drawRankBars('rankCustomer', Object.entries(custSums).map(([k,v])=>({key:k,label:k,value:v})), {topN:5});

  const defSums = {}; rowsWithPeriod.forEach(r=>{ defSums[r[5]] = (defSums[r[5]]||0)+r[4]; });
  drawRankBars('rankDefect', Object.entries(defSums).map(([k,v])=>({key:k,label:k,value:v})), {topN:5});
}

/* ================= Page 2 : 원인 드릴다운 ================= */
function drawSmallMultiplesDynamic(rows, months, cats){
  const data = {};
  cats.forEach(c=>{ data[c]={}; months.forEach(m=>{ data[c][m]=0; }); });
  rows.forEach(r=>{
    const c=r[2], m=r[3];
    if(data[c] && data[c][m]!==undefined){ data[c][m]+=r[4]; }
  });
  let html='';
  cats.forEach(cat=>{
    const vals = months.map(m=>data[cat][m]);
    const max=Math.max.apply(null, vals.concat([0])), min=Math.min.apply(null, vals.concat([0]));
    const W=200,H=44,pad=4;
    const pts = vals.map((v,i)=>{
      const x = months.length>1 ? pad+(W-2*pad)*(i/(months.length-1)) : W/2;
      const y = H-pad-(H-2*pad)*((v-min)/((max-min)||1));
      return x+','+y;
    }).join(' ');
    const half = Math.max(1, Math.floor(vals.length/2));
    const firstSum = vals.slice(0,half).reduce((a,b)=>a+b,0);
    const secondSum = vals.slice(half).reduce((a,b)=>a+b,0);
    const pct = firstSum ? (secondSum-firstSum)/firstSum*100 : null;
    const total = vals.reduce((a,b)=>a+b,0);
    const active = filters.category===cat ? ' active' : '';
    html += '<div class="sm-card'+active+'" data-cat="'+cat+'">'
      +'<div class="sm-title">'+(CAT_KOR[cat]||cat)+'</div>'
      +'<svg class="sm-spark" viewBox="0 0 '+W+' '+H+'"><polyline points="'+pts+'" fill="none" stroke="#1f4e79" stroke-width="2"></polyline></svg>'
      +'<div class="sm-foot"><span class="sm-amt">'+fmtUSD(total)+'</span>'+pctBadge(pct)+'</div>'
      +'<div class="sm-cap">선택 기간 전반부 대비 후반부</div></div>';
  });
  document.getElementById('smallMultiples').innerHTML = html;
  document.querySelectorAll('#smallMultiples .sm-card').forEach(el=>{
    el.addEventListener('click', ()=>{
      const cat = el.dataset.cat;
      filters.category = (filters.category===cat) ? '전체' : cat;
      syncFilterUI();
      rebuildAll();
    });
  });
}

function drawHeatmapDynamic(rows, plants, defects){
  const values = plants.map(()=>defects.map(()=>0));
  const pIdx={}; plants.forEach((p,i)=>{ pIdx[p]=i; });
  const dIdx={}; defects.forEach((d,i)=>{ dIdx[d]=i; });
  rows.forEach(r=>{
    const p=r[1], d=r[5];
    if(pIdx[p]!==undefined && dIdx[d]!==undefined){ values[pIdx[p]][dIdx[d]]++; }
  });
  const flat = values.reduce((a,row)=>a.concat(row), []);
  const max = maxOf(flat);
  let thead = '<tr><th></th>' + defects.map(d=>'<th><span>'+d+'</span></th>').join('') + '</tr>';
  let rowsHtml='';
  plants.forEach((p,ri)=>{
    let cells = values[ri].map(v=>{
      const t = max>0 ? v/max : 0;
      const bg = 'rgba(22,50,79,'+(0.06+t*0.78).toFixed(2)+')';
      const color = t>0.55? '#fff':'#1c2430';
      return '<td style="background:'+bg+';color:'+color+'">'+v+'</td>';
    }).join('');
    rowsHtml += '<tr><th class="row-h">'+p+'</th>'+cells+'</tr>';
  });
  document.getElementById('heatmapTable').innerHTML = '<thead>'+thead+'</thead><tbody>'+rowsHtml+'</tbody>';
}

function rebuildPage2(rows){
  const months = ALL_MONTHS.filter(m=>m>=periodMinYm(filters.period));
  const catsToShow = filters.category==='전체' ? ALL_CATEGORIES : [filters.category];
  drawSmallMultiplesDynamic(rows, months, catsToShow);

  const plantsToShow = filters.plant==='전체' ? ALL_PLANTS : [filters.plant];
  drawHeatmapDynamic(rows, plantsToShow, ALL_DEFECTS);

  const catSums = {}; ALL_CATEGORIES.forEach(c=>{ catSums[c]=0; });
  rows.forEach(r=>{ catSums[r[2]] += r[4]; });
  drawRankBars('rankCategory', ALL_CATEGORIES.map(c=>({key:c, label:CAT_KOR[c]||c, value:catSums[c]})), {clickField:'category'});

  const defCounts = {}; ALL_DEFECTS.forEach(d=>{ defCounts[d]=0; });
  rows.forEach(r=>{ defCounts[r[5]] += 1; });
  drawRankBars('rankDefectCount', ALL_DEFECTS.map(d=>({key:d, label:d, value:defCounts[d]})), {topN:10, fmt:fmtCount});

  const custSums = {}; ALL_CUSTOMERS.forEach(c=>{ custSums[c]=0; });
  rows.forEach(r=>{ custSums[r[0]] += r[4]; });
  drawRankBars('custComposition', ALL_CUSTOMERS.map(c=>({key:c, label:c, value:custSums[c]})), {clickField:'customer'});
}

/* ================= Page 3 : 리드타임 & 효율 ================= */
function drawStatusBar(rows){
  const sc = {}; STATUS_ORDER.forEach(k=>{ sc[k]=0; });
  rows.forEach(r=>{ sc[r[7]] = (sc[r[7]]||0)+1; });
  const total = rows.length || 1;
  let segs='', legend='';
  STATUS_ORDER.forEach(k=>{
    const w = sc[k]/total*100;
    segs += '<div class="seg" style="width:'+w+'%;background:'+STATUS_COLOR[k]+'" title="'+k+': '+sc[k]+'건 ('+w.toFixed(1)+'%)"></div>';
    legend += '<div class="legend-item"><span class="dot" style="background:'+STATUS_COLOR[k]+'"></span>'+k+' '+sc[k]+'건 ('+w.toFixed(1)+'%)</div>';
  });
  document.getElementById('statusBar').innerHTML = segs;
  document.getElementById('statusLegend').innerHTML = legend;
  const openCount = (sc['접수']||0)+(sc['조사중']||0);
  const openPct = rows.length ? round1(openCount/rows.length*100) : 0;
  document.getElementById('openCallout').innerHTML = rows.length
    ? '현재 <b>미결(접수+조사중) '+openCount.toLocaleString()+'건</b> ('+openPct+'%)이 처리 대기 중입니다.'
    : '해당 조건의 데이터가 없습니다.';
}

function drawSeverity(rows){
  const cnt={}, amt={}; SEV_ORDER.forEach(k=>{ cnt[k]=0; amt[k]=0; });
  rows.forEach(r=>{ cnt[r[8]] = (cnt[r[8]]||0)+1; amt[r[8]] = (amt[r[8]]||0)+r[4]; });
  const totalCnt = rows.length || 1;
  const totalAmt = rows.reduce((s,r)=>s+r[4],0) || 1;
  let html='';
  SEV_ORDER.forEach(k=>{
    const cp=(cnt[k]/totalCnt*100).toFixed(1);
    const ap=(amt[k]/totalAmt*100).toFixed(1);
    html += '<div class="sev-row">'
      +'<div class="sev-label"><span class="dot" style="background:'+SEV_COLOR[k]+'"></span>'+k+'</div>'
      +'<div class="sev-stats">'+cnt[k].toLocaleString()+'건 ('+cp+'%) · '+fmtUSD(amt[k])+' ('+ap+'%)</div>'
      +'<div class="sev-bar-wrap"><div class="sev-bar" style="width:'+ap+'%;background:'+SEV_COLOR[k]+'"></div></div>'
      +'</div>';
  });
  document.getElementById('severityBlock').innerHTML = html;
}

function drawHistogram(svgId, values, edges, color, capId, capLabel){
  const vals = values.filter(v=>v!==null && v!==undefined);
  const counts = new Array(edges.length-1).fill(0);
  vals.forEach(v=>{
    for(let i=0;i<edges.length-1;i++){
      const isLast = i===edges.length-2;
      if(v>=edges[i] && (v<edges[i+1] || (isLast && v<=edges[i+1]))){ counts[i]++; break; }
    }
  });
  const W=460,H=220,padL=30,padR=16,padT=20,padB=34;
  const innerW=W-padL-padR, innerH=H-padT-padB;
  const max=maxOf(counts);
  const n=counts.length;
  const bw=innerW/n*0.8;
  let bars='';
  counts.forEach((c,i)=>{
    const x = padL + innerW*(i+0.5)/n - bw/2;
    const h = innerH*(c/max);
    const y = padT+innerH-h;
    bars += '<rect x="'+x+'" y="'+y+'" width="'+bw+'" height="'+h+'" fill="'+color+'" rx="2"></rect>';
    bars += '<text x="'+(x+bw/2)+'" y="'+(y-4)+'" font-size="9.5" fill="#6b7280" text-anchor="middle">'+c+'</text>';
    bars += '<text x="'+(x+bw/2)+'" y="'+(H-16)+'" font-size="9.5" fill="#8a93a3" text-anchor="middle">'+edges[i]+'-'+edges[i+1]+'</text>';
  });
  document.getElementById(svgId).innerHTML = bars;
  if(vals.length){
    const mean = round1(vals.reduce((a,b)=>a+b,0)/vals.length);
    const sorted = vals.slice().sort((a,b)=>a-b);
    const median = sorted[Math.floor(sorted.length/2)];
    document.getElementById(capId).innerHTML = capLabel+' 평균 <b>'+mean+'일</b> · 중앙값 <b>'+median+'일</b> (n='+vals.length+')';
  } else {
    document.getElementById(capId).innerHTML = '해당 조건의 데이터가 없습니다.';
  }
}

function avgCycleBy(rows, idx, universe){
  const sum={}, n={};
  rows.forEach(r=>{
    if(r[11]!==null){ const k=r[idx]; sum[k]=(sum[k]||0)+r[11]; n[k]=(n[k]||0)+1; }
  });
  return universe.filter(k=>n[k]).map(k=>({key:k,label:k,value:round1(sum[k]/n[k])}));
}

function rebuildPage3(rows){
  drawStatusBar(rows);
  drawSeverity(rows);
  drawHistogram('histReceive', rows.map(r=>r[9]), RECEIVE_EDGES, '#1f4e79', 'histReceiveCap', '발생→접수');
  drawHistogram('histConfirm', rows.map(r=>r[10]), CONFIRM_EDGES, '#2a7f62', 'histConfirmCap', '접수→확정');
  drawRankBars('custCycle', avgCycleBy(rows,0,ALL_CUSTOMERS), {fmt:fmtDays});
  drawRankBars('plantCycle', avgCycleBy(rows,1,ALL_PLANTS), {fmt:fmtDays});
}

/* ================= Orchestration ================= */
function rebuildAll(){
  const rowsNoPeriod = filteredRows(true);
  const rowsWithPeriod = filteredRows(false);
  updateReadouts(rowsWithPeriod);
  rebuildPage1(rowsNoPeriod, rowsWithPeriod);
  rebuildPage2(rowsWithPeriod);
  rebuildPage3(rowsWithPeriod);
}

populateFilters();
syncFilterUI();
rebuildAll();
</script>
</body>
</html>
"""

FILTER_BAR_HTML = r"""<div class="filter-bar">
        <div class="filter-field"><label>고객사</label><select class="f-customer"><option value="전체">전체</option></select></div>
        <div class="filter-field"><label>생산공장</label><select class="f-plant"><option value="전체">전체</option></select></div>
        <div class="filter-field"><label>부품 카테고리</label><select class="f-category"><option value="전체">전체</option></select></div>
        <div class="filter-field"><label>기간</label>
          <select class="f-period">
            <option value="all">전체 기간 (2023.01~2025.12)</option>
            <option value="12m">최근 12개월</option>
            <option value="6m">최근 6개월</option>
            <option value="3m">최근 3개월</option>
          </select>
        </div>
        <button class="filter-reset" type="button">필터 초기화</button>
        <div class="filter-readout"></div>
      </div>"""

out = (TEMPLATE
       .replace("__FILTER_BAR__", FILTER_BAR_HTML)
       .replace("__WORLDMAP__", WORLDMAP_SVG)
       .replace("__ROWS_JSON__", ROWS_JSON)
       .replace("__LOGO_B64__", LOGO_B64))

with open("대시보드 기획안.html", "w", encoding="utf-8") as f:
    f.write(out)

print("wrote", len(out), "bytes")
