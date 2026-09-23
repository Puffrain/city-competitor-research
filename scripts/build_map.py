#!/usr/bin/env python3
"""Build the interactive Amap HTML map from a competitor JSON dump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<style>
  html,body{margin:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#1b1b1b;background:#efeae1;}
  #wrap{display:grid;grid-template-columns:360px 1fr;height:100%;}
  #side{background:#fff;border-right:1px solid #e4ddd0;overflow:auto;padding:12px 14px 24px;}
  #map{position:relative;min-height:420px;}
  h1{margin:0;font-size:17px;}
  .meta{margin:4px 0 0;font-size:12px;color:#666;line-height:1.45;}
  .group{margin:14px 0 6px;font-size:12px;font-weight:700;letter-spacing:.04em;}
  .row{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:13px;}
  .row input{margin:0;}
  .count{color:#777;font-weight:500;}
  input[type=search], input[type=text], select{
    width:100%;box-sizing:border-box;padding:7px 9px;border:1px solid #d7d1c4;border-radius:6px;font-size:13px;background:#fff;
  }
  .actions{display:flex;gap:6px;margin:8px 0 4px;flex-wrap:wrap;}
  button{font-size:12px;padding:6px 9px;border:1px solid #d7d1c4;background:#faf8f3;border-radius:6px;cursor:pointer;}
  button.primary{background:#1d4ed8;color:#fff;border-color:#1d4ed8;}
  #list{max-height:220px;overflow:auto;border:1px solid #f1ece3;border-radius:8px;padding:0 8px;margin:8px 0;}
  .store{display:flex;align-items:flex-start;gap:6px;padding:6px 0;font-size:12px;border-bottom:1px solid #f1ece3;cursor:pointer;}
  .store b{min-width:22px;}
  .p1{color:#C2410C;} .p2{color:#1D4ED8;} .p3{color:#0F766E;}
  .mk{position:relative;width:28px;height:32px;}
  .mk .head{width:20px;height:20px;margin:0 auto;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;color:#fff;font:700 10px/1 -apple-system,"PingFang SC",sans-serif;}
  .mk .tip{width:0;height:0;margin:-1px auto 0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:10px solid currentColor;filter:drop-shadow(0 1px 1px rgba(0,0,0,.2));}
  .mk .lab{position:absolute;left:26px;top:0;background:#fff;border:1px solid #e5e1d8;border-radius:4px;padding:1px 6px;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.16);font:12px/1.3 -apple-system,"PingFang SC",sans-serif;color:#111;}
  .mk .lab b{font-weight:700;}
  .mk .lab em{font-style:normal;margin-left:4px;font-weight:700;}
  .mk.active .head{box-shadow:0 0 0 3px rgba(17,17,17,.2),0 1px 4px rgba(0,0,0,.35);}
  .origin-mk{width:16px;height:16px;border-radius:50%;background:#111;border:3px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.4);}
  .origin-mk:after{content:"";position:absolute;left:50%;top:16px;margin-left:-6px;border:6px solid transparent;border-top-color:#111;}
  body.drop-mode #map{cursor:crosshair;}
  button.on-drop{background:#111;color:#fff;border-color:#111;}
  .near-mk{position:relative;width:14px;height:14px;}
  .near-mk i{display:block;width:12px;height:12px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);}
  .near-mk .lab{position:absolute;left:16px;top:-3px;background:#fff;border:1px solid #e5e1d8;border-radius:4px;padding:1px 5px;white-space:nowrap;font:11px/1.3 -apple-system,"PingFang SC",sans-serif;box-shadow:0 1px 2px rgba(0,0,0,.12);}
  .leaflet-div-icon{background:transparent;border:0;}
  .near-item{font-size:12px;padding:8px 0;border-bottom:1px solid #f0ece3;cursor:pointer;}
  .near-item span{color:#777;}
  .near-item a{color:#1d4ed8;margin-right:8px;}
  .searchbar{position:absolute;z-index:500;left:14px;top:14px;right:14px;display:flex;gap:8px;max-width:560px;}
  .searchbar input{flex:1;padding:10px 12px;border:0;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.18);font-size:14px;}
  .searchbar button{padding:10px 12px;border:0;border-radius:8px;background:#1d4ed8;color:#fff;box-shadow:0 8px 24px rgba(0,0,0,.18);}
  .hint{position:absolute;z-index:500;left:14px;bottom:18px;background:rgba(255,255,255,.92);padding:8px 10px;border-radius:8px;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,.12);max-width:460px;}
  .card{margin-top:12px;padding:10px;border:1px solid #e5e1d8;border-radius:8px;background:#faf8f3;}
  .card h2{margin:0 0 6px;font-size:14px;}
  .kv{display:grid;grid-template-columns:64px 1fr;gap:4px 8px;font-size:12px;}
  .kv b{color:#666;font-weight:600;}
  .card a{color:#1d4ed8;margin-right:8px;font-size:12px;}
  .tabs{display:flex;gap:4px;margin:10px 0 6px;}
  .tabs button{flex:1;}
  .tabs button.on{background:#1d4ed8;color:#fff;border-color:#1d4ed8;}
  .note{font-size:11px;color:#888;line-height:1.4;margin:6px 0;}
  .radius-row{display:flex;gap:6px;align-items:center;margin:8px 0;flex-wrap:wrap;}
  .radius-row select, .radius-row input{width:auto;flex:1;min-width:90px;}
  .chips{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 8px;}
  .chips button.on{background:#1d4ed8;color:#fff;border-color:#1d4ed8;}
  .popup{min-width:180px;font:12px/1.45 -apple-system,"PingFang SC",sans-serif;}
  .popup img{width:100%;height:88px;object-fit:cover;border-radius:6px;margin:0 0 6px;background:#eee;}
  @media (max-width: 860px){
    #wrap{grid-template-columns:1fr;grid-template-rows:42vh 1fr;}
    #side{border-right:0;border-top:1px solid #e4ddd0;}
    .searchbar{right:70px;}
  }
</style>
</head>
<body>
<div id="wrap">
  <aside id="side">
    <h1>__TITLE__</h1>
    <p class="meta">点一家店，或自己在地图上落一个点，按半径看附近小区、学校、商圈。蓝色线是__CITY__边界。</p>
    <label class="row"><input type="checkbox" id="f-bound" checked><span>显示__CITY__轮廓</span></label>
    <div class="group">看哪些竞品</div>
    <label class="row"><input type="checkbox" id="f-P1" checked><span class="p1">P1 优先深挖</span> <span class="count" id="c-P1"></span></label>
    <label class="row"><input type="checkbox" id="f-P2" checked><span class="p2">P2 核心补全</span> <span class="count" id="c-P2"></span></label>
    <label class="row"><input type="checkbox" id="f-P3" checked><span class="p3">P3 相邻入口</span> <span class="count" id="c-P3"></span></label>
    <div class="actions">
      <button type="button" id="onlyp1">只看 P1</button>
      <button type="button" id="all">全看</button>
      <button type="button" id="none">先清空</button>
    </div>
    <input id="q" type="search" placeholder="筛店名、品牌、地址">
    <div id="list"></div>
    <div id="card" class="card">点地图图钉或左侧店名，看这家店和附近范围。</div>
    <div class="group">附近范围</div>
    <div class="chips" id="radius-chips">
      <button type="button" data-m="100">100 米</button>
      <button type="button" data-m="500">500 米</button>
      <button type="button" data-m="1000">1 公里</button>
      <button type="button" data-m="3000" class="on">3 公里</button>
    </div>
    <div class="radius-row">
      <input id="radius-custom" type="number" min="50" max="50000" step="50" placeholder="自己填米数，如 800">
      <button type="button" id="radius-apply">按这个查</button>
    </div>
    <div class="actions">
      <button type="button" id="drop-point">在地图上自己加点</button>
    </div>
    <p class="note" id="drop-hint">点上面这个按钮后，再点地图空白处，会以那个点为中心查附近。</p>
    <label class="row"><input type="checkbox" id="l-xiaoqu" checked><span>小区名称</span></label>
    <label class="row"><input type="checkbox" id="l-mall" checked><span>商场 / 商圈名称</span></label>
    <div class="group">学校类型</div>
    <label class="row"><input type="checkbox" id="s-kinder" checked><span>幼儿园</span></label>
    <label class="row"><input type="checkbox" id="s-primary" checked><span>小学</span></label>
    <label class="row"><input type="checkbox" id="s-junior" checked><span>初中</span></label>
    <label class="row"><input type="checkbox" id="s-senior" checked><span>高中</span></label>
    <label class="row"><input type="checkbox" id="s-other" checked><span>其他学校</span></label>
    <div class="tabs">
      <button type="button" class="on" data-tab="xiaoqu">小区</button>
      <button type="button" data-tab="school">学校</button>
      <button type="button" data-tab="mall">商场商圈</button>
    </div>
    <p class="note">高德没有地块红线和挂牌均价。地图只标名称图钉，不画小区/学校/商圈范围圈。房价给贝壳 / 安居客 / 百度检索。</p>
    <div class="actions">
      <button type="button" class="primary" id="near-btn">刷新附近</button>
      <button type="button" id="near-clear">清掉附近结果</button>
    </div>
    <div id="near-list" class="meta">先点一家店。</div>
  </aside>
  <div id="map">
    <div class="searchbar">
      <input id="map-q" type="search" placeholder="也可临时搜：地铁站、幼儿园…">
      <button type="button" id="map-search">搜索</button>
    </div>
    <div class="hint" id="hint">点一家店，或自己在地图上加一个点，按半径看附近小区、学校、商圈。</div>
  </div>
</div>
<script src="amap-key.js"></script>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
function readKey(){
  const q = new URLSearchParams(location.search).get("key");
  if (q) return q;
  try { if (localStorage.AMAP_MAPS_API_KEY) return localStorage.AMAP_MAPS_API_KEY; } catch (e) {}
  return window.AMAP_MAPS_API_KEY || "";
}
const KEY = readKey();
const CITY = "__CITY__";
const cityBound = __BOUND__;
const pts = __PTS__;
const colors = {P1:"#C2410C", P2:"#1D4ED8", P3:"#0F766E"};
const tabColor = {xiaoqu:"#0F766E", school:"#1D4ED8", mall:"#C2410C"};
const selected = Object.fromEntries(pts.map(d => [d.no, true]));
let current = null;
let origin = null;
let originMarker = null;
let dropMode = false;
let catchment = null;
let activeTab = "xiaoqu";
let searchRadius = 3000;
let catchmentToken = 0;
const nearCache = {xiaoqu:[], school:[], mall:[]};
let fullNear = {key:"", xiaoqu:[], school:[], mall:[]};
const extraLayer = L.layerGroup();

function radiusLabel(m){
  m = Math.round(m);
  if (m >= 1000 && m % 1000 === 0) return (m/1000) + " 公里";
  if (m >= 1000) return (m/1000).toFixed(1).replace(/\.0$/, "") + " 公里";
  return m + " 米";
}
function clampRadius(v){
  const n = Number(v);
  if (!Number.isFinite(n)) return 3000;
  return Math.max(50, Math.min(50000, Math.round(n)));
}
function syncRadiusChips(){
  document.querySelectorAll("#radius-chips button").forEach(b => {
    b.classList.toggle("on", Number(b.dataset.m) === searchRadius);
  });
  const box = document.getElementById("radius-custom");
  if (box && document.activeElement !== box) box.value = searchRadius;
}
function setRadius(m, reload){
  searchRadius = clampRadius(m);
  syncRadiusChips();
  if (reload && current) applyRadius(current);
}

const map = L.map("map", {zoomControl:true, maxZoom:18}).setView(__CENTER__, 12);
L.tileLayer("https://wprd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scl=1&style=7&x={x}&y={y}&z={z}", {
  subdomains: "1234", minZoom: 9, maxZoom: 18, attribution: "高德地图"
}).addTo(map);
L.control.scale({imperial:false}).addTo(map);
const boundLayer = L.polygon(cityBound, {
  color:"#1d4ed8", weight:2.5, opacity:0.95, fillColor:"#1d4ed8", fillOpacity:0.05, interactive:false
}).addTo(map);
map.fitBounds(boundLayer.getBounds(), {padding:[20,20], maxZoom:12});
const shopLayer = L.layerGroup().addTo(map);
const nearLayer = L.layerGroup().addTo(map);
extraLayer.addTo(map);
const nearList = document.getElementById("near-list");
const hint = document.getElementById("hint");
const card = document.getElementById("card");

function f(id){ return document.getElementById(id).checked; }
function visiblePts(){
  const pOn = {P1: f("f-P1"), P2: f("f-P2"), P3: f("f-P3")};
  const q = document.getElementById("q").value.trim().toLowerCase();
  return pts.filter(d => pOn[d.p] && selected[d.no] && (!q || (d.name + d.lab + d.addr + (d.brand||"")).toLowerCase().includes(q)));
}
function setOrigin(lat, lon, label, zoom, showDot){
  origin = {lat, lon, label};
  if (originMarker) { map.removeLayer(originMarker); originMarker = null; }
  if (showDot) {
    originMarker = L.marker([lat, lon], {
      icon: L.divIcon({className:"", html:'<div class="origin-mk"></div>', iconSize:[18,18], iconAnchor:[9,9]}),
      zIndexOffset: 500, interactive: false
    }).addTo(map);
  }
  if (zoom) map.setView([lat, lon], Math.max(map.getZoom(), zoom));
}
function setDropMode(on){
  dropMode = !!on;
  document.body.classList.toggle("drop-mode", dropMode);
  const btn = document.getElementById("drop-point");
  if (btn) btn.classList.toggle("on-drop", dropMode);
  const hintEl = document.getElementById("drop-hint");
  if (hintEl) hintEl.textContent = dropMode ? "现在点地图空白处，会以那个点为中心查附近。再点一次按钮可取消。" : "点上面这个按钮后，再点地图空白处，会以那个点为中心查附近。";
}
function customPoint(lat, lon){
  return {
    no: "custom", p: "P2", name: "自选点", lab: "自选点",
    brand: "自选点", addr: lat.toFixed(6) + ", " + lon.toFixed(6),
    tel: "", hours: "", rating: "", area: "", type: "地图自选点",
    amap: "", dianping: "", baidu: "", lat, lon
  };
}
function dropAt(lat, lon){
  setDropMode(false);
  current = customPoint(lat, lon);
  setOrigin(lat, lon, "自选点", 16, true);
  drawShops();
  renderCard(current);
  loadCatchment(current, true);
}
function val(v){ return v && String(v).trim() && v !== "未查到" ? v : "未查到"; }
function link(href, text){ return href ? `<a href="${href}" target="_blank" rel="noopener">${text}</a>` : ""; }
function renderCard(d){
  if (!d) { card.textContent = "点一家店，或自己在地图上加一个点。"; return; }
  const title = d.no === "custom" ? "自选点" : (d.p + "  " + d.lab);
  card.innerHTML = `<h2>${title}</h2>
    <div class="kv">
      <b>门店</b><span>${d.name||""}</span>
      <b>品牌</b><span>${d.brand||d.lab||""}</span>
      <b>地址</b><span>${d.addr||"未查到"}</span>
      <b>电话</b><span>${val(d.tel)}</span>
      <b>时间</b><span>${val(d.hours)}</span>
      <b>评分</b><span>${d.rating ? d.rating + "（高德，不当教学质量）" : "未查到"}</span>
      <b>商圈</b><span>${d.area||"未标注"}</span>
      <b>类型</b><span>${d.type||"未查到"}</span>
    </div>
    <div style="margin-top:8px">${link(d.amap,"高德")}${link(d.dianping,"点评")}${link(d.baidu,"百度")}</div>
    <div class="actions"><button type="button" class="primary" id="card-near">按当前半径看附近小区 / 学校 / 商场</button></div>`;
  const btn = document.getElementById("card-near");
  if (btn) btn.onclick = () => loadCatchment(d);
}
function show(d){
  current = d;
  setOrigin(d.lat, d.lon, d.lab, 15, false);
  drawShops();
  renderCard(d);
  loadCatchment(d);
}
function drawShops(){
  shopLayer.clearLayers();
  visiblePts().forEach(d => {
    const on = current && current.no === d.no ? " active" : "";
    const html = `<div class="mk${on}" style="color:${colors[d.p]}"><div class="head" style="background:${colors[d.p]}">${d.p.replace("P","")}</div><div class="tip"></div><div class="lab"><b>${d.lab}</b><em style="color:${colors[d.p]}">${d.p}</em></div></div>`;
    const icon = L.divIcon({className:"", html, iconSize:[28,36], iconAnchor:[14,36]});
    const m = L.marker([d.lat, d.lon], {icon, zIndexOffset: (current && current.no===d.no)?450:(d.p==="P1"?300:200)});
    m.on("click", () => show(d));
    m.addTo(shopLayer);
  });
  ["P1","P2","P3"].forEach(k => {
    document.getElementById("c-"+k).textContent = "(" + pts.filter(d => d.p===k && selected[d.no]).length + ")";
  });
}
function renderList(){
  const q = document.getElementById("q").value.trim().toLowerCase();
  const pOn = {P1: f("f-P1"), P2: f("f-P2"), P3: f("f-P3")};
  const box = document.getElementById("list");
  box.innerHTML = "";
  pts.filter(d => pOn[d.p] && (!q || (d.name + d.lab + d.addr + (d.brand||"")).toLowerCase().includes(q))).forEach(d => {
    const row = document.createElement("div");
    row.className = "store";
    row.innerHTML = `<input type="checkbox" ${selected[d.no]?"checked":""}><b class="${d.p.toLowerCase()}">${d.p}</b><span>${d.lab}<br><span style="color:#777">${d.name}</span></span>`;
    row.querySelector("input").addEventListener("change", e => { selected[d.no]=e.target.checked; drawShops(); });
    row.addEventListener("click", ev => { if (ev.target.tagName !== "INPUT") show(d); });
    box.appendChild(row);
  });
  drawShops();
}
function jsonp(url){
  return new Promise((resolve, reject) => {
    const cb = "amapCb" + Date.now() + Math.floor(Math.random()*999);
    const s = document.createElement("script");
    const timer = setTimeout(() => { cleanup(); reject(new Error("timeout")); }, 12000);
    function cleanup(){ clearTimeout(timer); delete window[cb]; s.remove(); }
    window[cb] = data => { cleanup(); resolve(data); };
    s.onerror = () => { cleanup(); reject(new Error("script")); };
    s.src = url + (url.includes("?") ? "&" : "?") + "callback=" + cb;
    document.body.appendChild(s);
  });
}
function sleep(ms){ return new Promise(resolve => setTimeout(resolve, ms)); }
let amapQueue = Promise.resolve();
function enqueueAmap(fn){
  const run = amapQueue.then(fn, fn);
  amapQueue = run.catch(() => {});
  return run;
}
function amapLimited(data){
  const info = String((data && (data.info || data.infocode)) || "");
  return /CUQPS_HAS_EXCEEDED_THE_LIMIT|USER_DAILY_QUERY_OVER_LIMIT|OVER/.test(info);
}
async function amapAround(lat, lon, kw, radius, page){
  if (!KEY) throw new Error("missing-key");
  return enqueueAmap(async () => {
    const qs = "key=" + KEY + "&location=" + lon + "," + lat + "&keywords=" + encodeURIComponent(kw) + "&radius=" + radius + "&offset=25&page=" + (page||1) + "&extensions=all&output=json";
    const url = "https://restapi.amap.com/v3/place/around?" + qs;
    let last = {pois:[]};
    for (let attempt = 0; attempt < 4; attempt++) {
      if (attempt) await sleep(400 * attempt);
      else await sleep(180);
      try {
        const r = await fetch(url);
        const data = await r.json();
        if (data && data.status === "1") return data;
        last = data || last;
        if (amapLimited(data)) continue;
        break;
      } catch (e) {}
      try {
        const data = await jsonp(url);
        if (data && data.status === "1") return data;
        last = data || last;
        if (amapLimited(data)) continue;
      } catch (e) {}
    }
    return last && last.pois ? last : {pois:[]};
  });
}
function asText(v){
  if (v == null || v === "" || (Array.isArray(v) && !v.length)) return "";
  if (Array.isArray(v)) return v.filter(Boolean).join("；");
  if (typeof v === "object") return "";
  return String(v);
}
function parsePoi(p, kind){
  const loc = (p.location || "").split(",");
  if (loc.length !== 2) return null;
  const lat = +loc[1], lon = +loc[0];
  if (!lat || !lon) return null;
  const biz = p.biz_ext || {};
  let elat = null, elon = null;
  const entr = asText(p.entr_location);
  if (entr.includes(",")) {
    const e = entr.split(",");
    elon = +e[0]; elat = +e[1];
  }
  const photos = Array.isArray(p.photos) ? p.photos.map(x => x && x.url).filter(Boolean) : [];
  return {
    id: p.id || (p.name + loc.join(",")),
    name: p.name || "",
    addr: asText(p.address),
    type: p.type || "",
    typecode: p.typecode || "",
    area: asText(p.business_area),
    adname: asText(p.adname),
    tel: asText(p.tel),
    dist: p.distance ? Math.round(+p.distance) : null,
    rating: asText(biz.rating),
    hours: asText(biz.open_time) || asText(biz.opentime2),
    photo: photos[0] || "",
    lat, lon, elat, elon, kind,
    schoolLevel: kind === "school" ? schoolLevel({name: p.name || "", type: p.type || "", typecode: p.typecode || ""}) : ""
  };
}
function hasCode(p, prefixes){
  const codes = String(p.typecode || "").split("|");
  return codes.some(c => prefixes.some(pre => c.startsWith(pre)));
}
function schoolLevel(p){
  const t = ((p.type || "") + (p.name || "") + (p.typecode || ""));
  if (/141204/.test(p.typecode||"") || /幼儿园|幼稚园|学前/.test(t)) return "kinder";
  if (/141203/.test(p.typecode||"") || /小学/.test(t)) return "primary";
  if (/高中|高级中学|完中/.test(t)) return "senior";
  if (/141202/.test(p.typecode||"") || /初中|初级中学|中学/.test(t)) return "junior";
  return "other";
}
function schoolOn(level){
  const id = {kinder:"s-kinder", primary:"s-primary", junior:"s-junior", senior:"s-senior", other:"s-other"}[level] || "s-other";
  const el = document.getElementById(id);
  return el ? el.checked : true;
}
function schoolLabel(level){
  return {kinder:"幼儿园", primary:"小学", junior:"初中", senior:"高中", other:"其他学校"}[level] || "其他学校";
}
function keepPoi(p, kind){
  const name = p.name || "";
  const t = (p.type || "") + name;
  if (/培训机构|托管|托管班|课后|兴趣班|舞蹈|主持|琴行/.test(t) && kind !== "mall") return false;
  if (kind === "xiaoqu") {
    if (hasCode(p, ["1203"])) return !/写字楼|商务楼|宿舍|公寓酒店/.test(t);
    return /住宅小区|住宅区/.test(t) && /小区|花园|苑|家园|府|里|村/.test(name);
  }
  if (kind === "school") {
    if (/培训|托管|机构|兴趣班|舞蹈|主持|琴行/.test(t)) return false;
    return hasCode(p, ["1412"]) || /学校;小学|学校;中学|学校;幼儿园|学校;高等院校|学校;职业技术学校/.test(p.type||"");
  }
  if (kind === "mall") {
    if (/号楼|停车场|化妆品|便利店|专卖店|写字楼|商住两用|楼宇/.test(t)) return false;
    if (hasCode(p, ["060101","060102"])) return true;
    if (hasCode(p, ["190700"])) return /商圈|广场|城|CBD|中心/.test(name) && !/路$/.test(name);
    return /购物中心|商业广场/.test(t);
  }
  return true;
}
function haversine(lat1, lon1, lat2, lon2){
  const rad = Math.PI / 180;
  const dLat = (lat2-lat1) * rad, dLon = (lon2-lon1) * rad;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*rad)*Math.cos(lat2*rad)*Math.sin(dLon/2)**2;
  return Math.round(6371000 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
}
async function fetchKind(lat, lon, kind, apiRadius){
  const queries = {
    xiaoqu: ["小区"],
    school: ["幼儿园", "小学", "中学"],
    mall: ["商场", "购物中心"]
  }[kind];
  const seen = new Map();
  for (const kw of queries) {
    for (let page = 1; page <= 2; page++) {
      const data = await amapAround(lat, lon, kw, apiRadius, page);
      const pois = data.pois || [];
      if (!pois.length) break;
      pois.forEach(raw => {
        const p = parsePoi(raw, kind);
        if (!p || !keepPoi(p, kind) || seen.has(p.id)) return;
        p.dist = p.dist != null ? p.dist : haversine(lat, lon, p.lat, p.lon);
        if (p.dist > apiRadius) return;
        seen.set(p.id, p);
      });
      if (pois.length < 25) break;
    }
  }
  return [...seen.values()].sort((a,b) => (a.dist||9e9) - (b.dist||9e9));
}
function withinRadius(items, r){
  return (items || []).filter(p => p.dist != null && p.dist <= r);
}
function drawCatchmentCircle(d, r){
  if (catchment) map.removeLayer(catchment);
  catchment = L.circle([d.lat, d.lon], {radius:r, color:"#111", weight:1.2, dashArray:"6 6", fillOpacity:0.03, interactive:false}).addTo(map);
  const pad = r <= 200 ? 80 : (r <= 800 ? 40 : 24);
  const maxZ = r <= 200 ? 18 : (r <= 800 ? 16 : 14);
  map.fitBounds(catchment.getBounds(), {padding:[pad,pad], maxZoom:maxZ});
}
function applyRadius(d){
  if (!d) return;
  const r = searchRadius;
  extraLayer.clearLayers();
  drawCatchmentCircle(d, r);
  nearCache.xiaoqu = withinRadius(fullNear.xiaoqu, r).slice(0, 40);
  nearCache.school = withinRadius(fullNear.school, r).filter(p => schoolOn(p.schoolLevel || schoolLevel(p))).slice(0, 40);
  nearCache.mall = withinRadius(fullNear.mall, r).slice(0, 40);
  setTab(activeTab);
  const schoolBits = ["kinder","primary","junior","senior","other"].filter(schoolOn).map(schoolLabel).join("/") || "未选学校类型";
  hint.textContent = d.lab + " 附近 " + radiusLabel(r) + "：小区 " + nearCache.xiaoqu.length + "，学校 " + nearCache.school.length + "（" + schoolBits + "），商场商圈 " + nearCache.mall.length + "。";
}
function priceLinks(name){
  const q = encodeURIComponent(CITY + " " + name + " 二手房 均价");
  const q2 = encodeURIComponent(name);
  const cityQ = encodeURIComponent(CITY + " " + name);
  return [
    link("https://www.baidu.com/s?wd="+q, "百度房价"),
    link("https://www.ke.com/ershoufang/rs"+q2+"/", "贝壳检索"),
    link("https://www.anjuke.com/sy-city.html?kw="+q2, "安居客检索"),
    link("https://www.amap.com/search?query="+cityQ, "高德地点")
  ].join(" ");
}
function popupHtml(p){
  const dist = p.dist != null ? p.dist + " 米" : "";
  const img = p.photo ? `<img src="${p.photo}" alt="">` : "";
  const price = p.kind === "xiaoqu" ? `<div>房价：接口没有挂牌均价，请点检索。</div><div>${priceLinks(p.name)}</div>` : "";
  const tel = p.tel ? `电话 ${p.tel}<br>` : "";
  const hours = p.hours ? `时间 ${p.hours}<br>` : "";
  const rating = p.rating ? `评分 ${p.rating}<br>` : "";
  const level = p.kind === "school" ? schoolLabel(p.schoolLevel || schoolLevel(p)) + " · " : "";
  return `<div class="popup">${img}<b>${p.name}</b><br>${dist} · ${level}${p.adname||""} ${p.area||""}<br>${p.addr||""}<br>${p.type||""}<br>${tel}${hours}${rating}${price}</div>`;
}
function drawNear(){
  nearLayer.clearLayers();
  ["xiaoqu","school","mall"].forEach(kind => {
    if (kind === "school") {
      if (!["kinder","primary","junior","senior","other"].some(schoolOn)) return;
    } else {
      const box = document.getElementById("l-"+kind);
      if (box && !box.checked) return;
    }
    const color = tabColor[kind];
    const dim = kind !== activeTab;
    (nearCache[kind] || []).forEach(p => {
      const prefix = p.kind === "school" ? schoolLabel(p.schoolLevel || schoolLevel(p)) + " " : "";
      const html = `<div class="near-mk"><i style="background:${color};opacity:${dim?0.55:1}"></i><div class="lab" style="opacity:${dim?0.85:1}">${prefix}${p.name}</div></div>`;
      const icon = L.divIcon({className:"", html, iconSize:[14,14], iconAnchor:[7,7]});
      L.marker([p.lat, p.lon], {icon, zIndexOffset: dim ? 40 : 90, opacity: dim ? 0.85 : 1}).bindPopup(popupHtml(p)).addTo(nearLayer);
    });
  });
}
function renderNearList(kind){
  const items = nearCache[kind] || [];
  const title = {xiaoqu:"小区", school:"学校", mall:"商场 / 商圈"}[kind];
  if (!origin) { nearList.textContent = "先点一家店，或自己在地图上加一个点。"; return; }
  if (!items.length) {
    nearList.textContent = origin.label + " 附近 " + radiusLabel(searchRadius) + " 没搜到" + title + "。";
    return;
  }
  nearList.innerHTML = `<b>${origin.label} 附近 ${radiusLabel(searchRadius)} ${title} ${items.length} 处</b>`;
  items.forEach(p => {
    const row = document.createElement("div");
    row.className = "near-item";
    const dist = p.dist != null ? p.dist + " 米" : "";
    const level = p.kind === "school" ? schoolLabel(p.schoolLevel || schoolLevel(p)) : "";
    const bits = [dist, level, p.adname, p.area, p.type].filter(Boolean).join(" · ");
    const extra = p.kind === "xiaoqu"
      ? `<div>房价未查到挂牌均价</div><div>${priceLinks(p.name)}</div>`
      : `<div>${p.tel ? "电话 "+p.tel+" · " : ""}${p.hours || p.rating ? ((p.hours||"") + (p.rating ? " · 评分 "+p.rating : "")) : ""}</div>`;
    row.innerHTML = `<b>${p.name}</b><br><span>${bits}</span>${p.addr ? "<br><span>"+p.addr+"</span>" : ""}${extra}`;
    row.onclick = () => { map.setView([p.lat, p.lon], 17); };
    nearList.appendChild(row);
  });
}
function setTab(kind){
  activeTab = kind;
  document.querySelectorAll(".tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === kind));
  drawNear();
  renderNearList(kind);
}
async function loadCatchment(d, force){
  if (!d) return;
  extraLayer.clearLayers();
  const r = searchRadius;
  const fetchR = Math.max(r, 3000);
  const cacheKey = d.no + "@" + fetchR;
  drawCatchmentCircle(d, r);
  if (!force && fullNear.key === cacheKey && (fullNear.xiaoqu.length || fullNear.school.length || fullNear.mall.length)) {
    applyRadius(d);
    return;
  }
  const token = ++catchmentToken;
  nearList.textContent = "正在查 " + d.lab + " 附近 " + radiusLabel(r) + " 小区、学校、商场…";
  hint.textContent = d.lab + " 附近 " + radiusLabel(r) + " 范围已画出。绿=小区，蓝=学校，橙=商场/商圈名称。";
  try {
    const xiaoqu = await fetchKind(d.lat, d.lon, "xiaoqu", fetchR);
    const school = await fetchKind(d.lat, d.lon, "school", fetchR);
    const mall = await fetchKind(d.lat, d.lon, "mall", fetchR);
    if (token !== catchmentToken) return;
    fullNear = {key: cacheKey, xiaoqu, school, mall};
    applyRadius(d);
  } catch (e) {
    if (token !== catchmentToken) return;
    nearList.textContent = e && e.message === "missing-key"
      ? "附近搜索需要高德 Web 服务 Key。可在地址后加 ?key=你的Key，或复制 amap-key.js.example 为 amap-key.js。"
      : "附近搜索暂时失败。请确认能上网，或用本地服务器打开这个网页。";
  }
}
function clearNear(){
  nearLayer.clearLayers();
  extraLayer.clearLayers();
  if (catchment) { map.removeLayer(catchment); catchment = null; }
  nearCache.xiaoqu = nearCache.school = nearCache.mall = [];
  fullNear = {key:"", xiaoqu:[], school:[], mall:[]};
  nearList.textContent = origin ? ("当前：" + origin.label + "。再点刷新。") : "先点一家店，或自己在地图上加一个点。";
}
function keyword(){ return (document.getElementById("map-q").value || "小学").trim(); }
async function searchCustom(){
  if (!origin) { nearList.textContent = "先点一家店，或自己在地图上加一个点。"; return; }
  const kw = keyword();
  nearList.textContent = "正在搜 " + origin.label + " 附近的「" + kw + "」…";
  extraLayer.clearLayers();
  try {
    const data = await amapAround(origin.lat, origin.lon, kw, Math.max(searchRadius, 3000));
    const pois = (data.pois || []).map(p => parsePoi(p, "mall")).filter(Boolean).map(p => {
      p.dist = p.dist != null ? p.dist : haversine(origin.lat, origin.lon, p.lat, p.lon);
      return p;
    }).filter(p => p.dist <= searchRadius).sort((a,b) => a.dist - b.dist);
    if (!pois.length) { nearList.textContent = "没搜到「" + kw + "」。"; return; }
    pois.slice(0, 20).forEach(p => {
      const icon = L.divIcon({className:"", html:`<div class="near-mk"><i style="background:#7c3aed"></i><div class="lab">${p.name}</div></div>`, iconSize:[14,14], iconAnchor:[7,7]});
      L.marker([p.lat, p.lon], {icon, zIndexOffset:60}).bindPopup(popupHtml(p)).addTo(extraLayer);
    });
    nearList.innerHTML = `<b>${origin.label} 附近临时搜索「${kw}」${Math.min(pois.length,20)} 处</b>`;
    pois.slice(0, 20).forEach(p => {
      const row = document.createElement("div");
      row.className = "near-item";
      row.innerHTML = `<b>${p.name}</b><br><span>${p.dist != null ? p.dist+" 米 · " : ""}${p.addr || p.type || ""}</span>`;
      row.onclick = () => map.setView([p.lat, p.lon], 17);
      nearList.appendChild(row);
    });
  } catch (e) {
    nearList.textContent = e && e.message === "missing-key" ? "缺少高德 Key。" : "搜索失败。";
  }
}
document.getElementById("f-bound").addEventListener("change", () => {
  if (document.getElementById("f-bound").checked) boundLayer.addTo(map);
  else map.removeLayer(boundLayer);
});
["f-P1","f-P2","f-P3"].forEach(id => document.getElementById(id).addEventListener("change", renderList));
["l-xiaoqu","l-mall"].forEach(id => document.getElementById(id).addEventListener("change", drawNear));
document.getElementById("q").addEventListener("input", renderList);
document.getElementById("all").onclick = () => { pts.forEach(d => selected[d.no]=true); document.getElementById("f-P1").checked=document.getElementById("f-P2").checked=document.getElementById("f-P3").checked=true; renderList(); };
document.getElementById("none").onclick = () => { pts.forEach(d => selected[d.no]=false); renderList(); };
document.getElementById("onlyp1").onclick = () => { document.getElementById("f-P1").checked=true; document.getElementById("f-P2").checked=false; document.getElementById("f-P3").checked=false; pts.forEach(d => selected[d.no]= d.p==="P1"); renderList(); };
document.getElementById("near-btn").onclick = () => current && loadCatchment(current, true);
document.getElementById("drop-point").onclick = () => setDropMode(!dropMode);
map.on("click", e => {
  if (!dropMode) return;
  if (e.originalEvent && e.originalEvent.target && e.originalEvent.target.closest(".leaflet-marker-icon")) return;
  dropAt(e.latlng.lat, e.latlng.lng);
});
["s-kinder","s-primary","s-junior","s-senior","s-other"].forEach(id => {
  document.getElementById(id).addEventListener("change", () => current && applyRadius(current));
});
document.querySelectorAll("#radius-chips button").forEach(b => b.addEventListener("click", () => setRadius(b.dataset.m, true)));
document.getElementById("radius-apply").onclick = () => setRadius(document.getElementById("radius-custom").value, true);
document.getElementById("radius-custom").addEventListener("keydown", e => { if (e.key === "Enter") setRadius(e.target.value, true); });
syncRadiusChips();
document.getElementById("near-clear").onclick = clearNear;
document.getElementById("map-search").onclick = searchCustom;
document.getElementById("map-q").addEventListener("keydown", e => { if (e.key === "Enter") searchCustom(); });
document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => setTab(b.dataset.tab)));
renderList();
</script>
</body>
</html>
"""


def pcode(priority: str) -> str:
    if str(priority).startswith("P1"):
        return "P1"
    if str(priority).startswith("P3"):
        return "P3"
    return "P2"


def text(v) -> str:
    if v is None or v in ([], "", "[]"):
        return ""
    if isinstance(v, list):
        return "".join(str(x) for x in v if x not in ([], None))
    return str(v)


def item_to_pt(it: dict, city: str) -> dict | None:
    lon, lat = it.get("lon"), it.get("lat")
    loc = text(it.get("location"))
    if (lon is None or lat is None) and "," in loc:
        try:
            lon, lat = (float(x) for x in loc.split(",", 1))
        except ValueError:
            lon = lat = None
    if lon is None or lat is None:
        return None
    name = text(it.get("name"))
    brand = text(it.get("brand")) or text(it.get("lab")) or name
    amap = text(it.get("amap"))
    if not amap and it.get("id"):
        amap = f"https://www.amap.com/place/{it['id']}"
    dianping = text(it.get("dianping")) or (
        "https://www.dianping.com/search/keyword/2/0_" + quote(name) if name else ""
    )
    baidu = text(it.get("baidu")) or (
        "https://www.baidu.com/s?wd=" + quote(f"{city} {name}") if name else ""
    )
    return {
        "no": it.get("no"),
        "p": pcode(it.get("priority") or "P2"),
        "name": name,
        "addr": text(it.get("address") or it.get("addr")),
        "lon": lon,
        "lat": lat,
        "lab": text(it.get("lab")) or brand[:12] or name[:12],
        "brand": brand,
        "tel": text(it.get("tel")),
        "hours": text(it.get("hours") or it.get("opentime")),
        "rating": text(it.get("rating")),
        "area": text(it.get("area") or it.get("business_area") or it.get("adname")),
        "type": text(it.get("type")),
        "amap": amap,
        "dianping": dianping,
        "baidu": baidu,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key", default="", help="ignored; maps do not embed secrets")
    args = ap.parse_args()
    data = json.loads(Path(args.in_json).read_text(encoding="utf-8"))
    city = data.get("city_name") or data.get("city") or "目标城市"
    pts = [p for it in (data.get("items") or []) if (p := item_to_pt(it, city))]
    bound = (data.get("boundary") or {}).get("rings") or []
    center = (data.get("boundary") or {}).get("center") or {}
    center_js = json.dumps([center.get("lat") or 31.23, center.get("lon") or 121.47])
    html = (
        TEMPLATE.replace("__TITLE__", f"{city}在营业竞品地图")
        .replace("__CITY__", city)
        .replace("__BOUND__", json.dumps(bound, ensure_ascii=False, separators=(",", ":")))
        .replace("__PTS__", json.dumps(pts, ensure_ascii=False, separators=(",", ":")))
        .replace("__CENTER__", center_js)
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"SAVED {out} points={len(pts)}", flush=True)


if __name__ == "__main__":
    main()
