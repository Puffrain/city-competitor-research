#!/usr/bin/env python3
"""Build the interactive Amap HTML map from a competitor JSON dump."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<style>
  html,body{margin:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#1b1b1b;background:#efeae1;}
  #wrap{display:grid;grid-template-columns:320px 1fr;height:100%;}
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
  .near-mk{position:relative;width:14px;height:14px;}
  .near-mk i{display:block;width:12px;height:12px;border-radius:50%;background:#ca8a04;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);}
  .near-mk .lab{position:absolute;left:16px;top:-3px;background:#fff8e8;border:1px solid #ca8a04;border-radius:4px;padding:1px 5px;white-space:nowrap;font:11px/1.3 -apple-system,"PingFang SC",sans-serif;box-shadow:0 1px 2px rgba(0,0,0,.12);}
  .origin-mk{position:relative;width:18px;height:18px;}
  .origin-mk i{display:block;width:14px;height:14px;margin:2px;border-radius:50%;background:#111;border:3px solid #fff;box-shadow:0 0 0 6px rgba(17,17,17,.16),0 1px 4px rgba(0,0,0,.3);}
  .leaflet-div-icon{background:transparent;border:0;}
  .near-item{font-size:12px;padding:6px 0;border-bottom:1px solid #f0ece3;cursor:pointer;}
  .near-item span{color:#777;}
  .searchbar{position:absolute;z-index:500;left:14px;top:14px;right:14px;display:flex;gap:8px;max-width:560px;}
  .searchbar input{flex:1;padding:10px 12px;border:0;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.18);font-size:14px;}
  .searchbar button{padding:10px 12px;border:0;border-radius:8px;background:#1d4ed8;color:#fff;box-shadow:0 8px 24px rgba(0,0,0,.18);}
  .hint{position:absolute;z-index:500;left:14px;bottom:18px;background:rgba(255,255,255,.92);padding:8px 10px;border-radius:8px;font-size:12px;box-shadow:0 4px 16px rgba(0,0,0,.12);max-width:360px;}
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
    <p class="meta">蓝色线是__CITY__边界。高德路网可放大到小区、道路。点一家店，或点地图空白处，再搜附近小学、小区。</p>
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
    <div class="group">附近搜什么</div>
    <input id="near-q" type="text" value="小学" placeholder="小学 / 幼儿园 / 小区 / 商场 / 地铁站">
    <div class="row" style="margin-top:8px;">
      <span>范围</span>
      <select id="near-r" style="width:auto;min-width:110px;">
        <option value="800">800 米</option>
        <option value="1500" selected>1.5 公里</option>
        <option value="3000">3 公里</option>
      </select>
    </div>
    <div class="actions">
      <button type="button" class="primary" id="near-btn">搜附近</button>
      <button type="button" id="near-center">按地图中心搜</button>
      <button type="button" id="near-clear">清掉附近结果</button>
    </div>
    <div id="near-list" class="meta">先点一家店，或点地图上任意位置，再搜附近。</div>
  </aside>
  <div id="map">
    <div class="searchbar">
      <input id="map-q" type="search" placeholder="搜附近：小学、幼儿园、小区、商场…">
      <button type="button" id="map-search">搜索</button>
    </div>
    <div class="hint" id="hint">滚轮放大可看到镇区和小区。黄标是附近搜索结果。</div>
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
const cityBound = __BOUND__;
const pts = __PTS__;
const colors = {P1:"#C2410C", P2:"#1D4ED8", P3:"#0F766E"};
const selected = Object.fromEntries(pts.map(d => [d.no, true]));
let current = pts[0] || null;
let origin = current ? {lat: current.lat, lon: current.lon, label: current.lab} : null;
let originMarker = null;
let circle = null;
const map = L.map("map", {zoomControl:true, maxZoom:18}).setView(__CENTER__, 12);
L.tileLayer("https://wprd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scl=1&style=7&x={x}&y={y}&z={z}", {
  subdomains: "1234", minZoom: 9, maxZoom: 18, attribution: "高德地图"
}).addTo(map);
L.control.scale({imperial:false}).addTo(map);
const boundLayer = L.polygon(cityBound, {
  color:"#1d4ed8", weight:2.5, opacity:0.95, fillColor:"#1d4ed8", fillOpacity:0.05,
  interactive:false
}).addTo(map);
map.fitBounds(boundLayer.getBounds(), {padding:[20,20], maxZoom:12});
const shopLayer = L.layerGroup().addTo(map);
const nearLayer = L.layerGroup().addTo(map);
const nearList = document.getElementById("near-list");
const hint = document.getElementById("hint");
function f(id){ return document.getElementById(id).checked; }
function visiblePts(){
  const pOn = {P1: f("f-P1"), P2: f("f-P2"), P3: f("f-P3")};
  const q = document.getElementById("q").value.trim().toLowerCase();
  return pts.filter(d => pOn[d.p] && selected[d.no] && (!q || (d.name + d.lab + d.addr).toLowerCase().includes(q)));
}
function setOrigin(lat, lon, label, zoom, showDot){
  origin = {lat, lon, label};
  if (originMarker) { map.removeLayer(originMarker); originMarker = null; }
  if (showDot) {
    originMarker = L.marker([lat, lon], {
      icon: L.divIcon({className:"", html:'<div class="origin-mk"><i></i></div>', iconSize:[18,18], iconAnchor:[9,9]}),
      zIndexOffset: 400, interactive: false
    }).addTo(map);
  }
  if (zoom) map.setView([lat, lon], Math.max(map.getZoom(), zoom));
  hint.textContent = "搜索中心：" + label + "。可改关键词后点搜索。";
}
function show(d){
  current = d;
  setOrigin(d.lat, d.lon, d.lab, 16, false);
  drawShops();
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
  pts.filter(d => pOn[d.p] && (!q || (d.name + d.lab + d.addr).toLowerCase().includes(q))).forEach(d => {
    const row = document.createElement("label");
    row.className = "store";
    row.innerHTML = `<input type="checkbox" ${selected[d.no]?"checked":""}><b class="${d.p.toLowerCase()}">${d.p}</b><span>${d.lab}<br><span style="color:#777">${d.name}</span></span>`;
    row.querySelector("input").addEventListener("change", e => { selected[d.no]=e.target.checked; drawShops(); });
    row.addEventListener("click", ev => { if (ev.target.tagName !== "INPUT") show(d); });
    box.appendChild(row);
  });
  drawShops();
}
function clearNear(){
  nearLayer.clearLayers();
  if (circle) { map.removeLayer(circle); circle = null; }
  nearList.textContent = origin ? ("当前中心：" + origin.label + "。再点搜索。") : "先点一家店或地图，再搜附近。";
}
function keyword(){
  return (document.getElementById("map-q").value || document.getElementById("near-q").value || "小学").trim();
}
function jsonp(url){
  return new Promise((resolve, reject) => {
    const cb = "amapCb" + Date.now();
    const s = document.createElement("script");
    const timer = setTimeout(() => { cleanup(); reject(new Error("timeout")); }, 12000);
    function cleanup(){ clearTimeout(timer); delete window[cb]; s.remove(); }
    window[cb] = data => { cleanup(); resolve(data); };
    s.onerror = () => { cleanup(); reject(new Error("script")); };
    s.src = url + (url.includes("?") ? "&" : "?") + "callback=" + cb;
    document.body.appendChild(s);
  });
}
async function amapAround(lat, lon, kw, radius){
  if (!KEY) throw new Error("missing-key");
  const qs = "key=" + KEY + "&location=" + lon + "," + lat + "&keywords=" + encodeURIComponent(kw) + "&radius=" + radius + "&offset=20&page=1&extensions=base&output=json";
  const url = "https://restapi.amap.com/v3/place/around?" + qs;
  try {
    const r = await fetch(url);
    const data = await r.json();
    if (data && data.status === "1") return data;
  } catch (e) {}
  return jsonp("https://restapi.amap.com/v3/place/around?" + qs);
}
async function searchNear(useCenter){
  const kw = keyword();
  document.getElementById("near-q").value = kw;
  document.getElementById("map-q").value = kw;
  if (useCenter) {
    const c = map.getCenter();
    current = null;
    setOrigin(c.lat, c.lng, "地图中心", 0, true);
    drawShops();
  }
  if (!origin) { nearList.textContent = "先点一家店，或点地图空白处。"; return; }
  const radius = document.getElementById("near-r").value;
  nearList.textContent = "正在搜 " + origin.label + " 附近的「" + kw + "」…";
  try {
    const data = await amapAround(origin.lat, origin.lon, kw, radius);
    nearLayer.clearLayers();
    if (circle) map.removeLayer(circle);
    circle = L.circle([origin.lat, origin.lon], {radius:+radius, color:"#1d4ed8", weight:1, fillOpacity:0.04}).addTo(map);
    const pois = data.pois || [];
    if (!pois.length) {
      nearList.textContent = origin.label + " 附近 " + (radius/1000) + " 公里没搜到「" + kw + "」。可换词或加大范围。";
      return;
    }
    nearList.innerHTML = "<b>" + origin.label + " 附近 " + pois.length + " 处「" + kw + "」</b>";
    pois.forEach(p => {
      const loc = (p.location || "").split(",");
      if (loc.length !== 2) return;
      const lat = +loc[1], lon = +loc[0];
      const dist = p.distance ? Math.round(p.distance) + " 米" : "";
      const icon = L.divIcon({className:"", html:`<div class="near-mk"><i></i><div class="lab">${p.name}</div></div>`, iconSize:[14,14], iconAnchor:[7,7]});
      L.marker([lat, lon], {icon, zIndexOffset:100}).addTo(nearLayer)
        .bindPopup("<b>" + (p.name || kw) + "</b><br>" + dist + "<br>" + (p.address || ""));
      const row = document.createElement("div");
      row.className = "near-item";
      row.innerHTML = `<b>${p.name}</b><br><span>${dist} · ${p.address || ""}</span>`;
      row.onclick = () => { map.setView([lat, lon], 17); };
      nearList.appendChild(row);
    });
    map.setView([origin.lat, origin.lon], Math.max(map.getZoom(), 15));
    hint.textContent = origin.label + " 附近「" + kw + "」" + pois.length + " 处。黄标可点开。";
  } catch (e) {
    nearList.textContent = e && e.message === "missing-key"
      ? "附近搜索需要高德 Web 服务 Key。可在地址后加 ?key=你的Key，或在控制台执行 localStorage.AMAP_MAPS_API_KEY='你的Key'。"
      : "附近搜索暂时失败。请确认能上网，或用本地服务器打开这个网页。";
  }
}
map.on("click", e => {
  current = null;
  setOrigin(e.latlng.lat, e.latlng.lng, "地图选点", 0, true);
  drawShops();
});
document.getElementById("f-bound").addEventListener("change", () => {
  if (document.getElementById("f-bound").checked) boundLayer.addTo(map);
  else map.removeLayer(boundLayer);
});
["f-P1","f-P2","f-P3"].forEach(id => document.getElementById(id).addEventListener("change", renderList));
document.getElementById("q").addEventListener("input", renderList);
document.getElementById("all").onclick = () => { pts.forEach(d => selected[d.no]=true); document.getElementById("f-P1").checked=document.getElementById("f-P2").checked=document.getElementById("f-P3").checked=true; renderList(); };
document.getElementById("none").onclick = () => { pts.forEach(d => selected[d.no]=false); renderList(); };
document.getElementById("onlyp1").onclick = () => { document.getElementById("f-P1").checked=true; document.getElementById("f-P2").checked=false; document.getElementById("f-P3").checked=false; pts.forEach(d => selected[d.no]= d.p==="P1"); renderList(); };
document.getElementById("near-btn").onclick = () => searchNear(false);
document.getElementById("near-center").onclick = () => searchNear(true);
document.getElementById("near-clear").onclick = clearNear;
document.getElementById("map-search").onclick = () => searchNear(false);
document.getElementById("map-q").addEventListener("keydown", e => { if (e.key === "Enter") searchNear(false); });
document.getElementById("near-q").addEventListener("keydown", e => { if (e.key === "Enter") searchNear(false); });
renderList();
if (current) setOrigin(current.lat, current.lon, current.lab, 0, false);
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key", default="", help="optional; maps should not embed secrets by default")
    args = ap.parse_args()
    data = json.loads(Path(args.in_json).read_text(encoding="utf-8"))
    city = data.get("city_name") or data.get("city") or "目标城市"
    pts = []
    for it in data.get("items") or []:
        if it.get("lat") is None or it.get("lon") is None:
            continue
        pts.append(
            {
                "no": it.get("no"),
                "p": pcode(it.get("priority") or "P2"),
                "name": it.get("name") or "",
                "addr": it.get("address") or "",
                "lon": it["lon"],
                "lat": it["lat"],
                "lab": it.get("lab") or it.get("brand") or it.get("name") or "",
            }
        )
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
