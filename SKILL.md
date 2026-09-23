---
name: city-competitor-research
description: Turn an industry plus one or more Chinese cities into an operating-competitor Word report and an interactive Amap HTML map. Use when the user asks to research 竞品, competitors, training schools, or nearby businesses in a city; when they say "行业 + 城市"; or when they want the Kunshan-style 竞品搜集报告 and 高德地图 workflow.
---

# 城市竞品搜集

用户只给行业和城市时，按昆山那套交付：一份可编辑 Word，一张可筛选、可点店看附近 3 公里小区/学校/商场的高德地图。只收在营。没查到写未查到，不编。

## 用户怎么说

- 「少儿编程，苏州」
- 「帮我做广州机器人教育竞品」
- 「按昆山那个工作流，再出上海」

缺城市或行业时问一句就够。多个城市就一座一座做，每城一份 Word、一张地图。

## 交付物

放到用户指定目录；没指定就放到当前项目的 `examples/` 或用户指定的调研目录：

1. `{城市}{行业}竞品详细搜集-在营业机构.docx`
2. `{城市}{行业}竞品地图-高德.html`
3. `{城市}{行业}-raw.json`（中间结果，不主动发给用户）

地图能力必须齐：高德路网、城市轮廓、P1/P2/P3 筛选、图钉、点店看附近 3 公里小区/学校/商场。

## 工作流

1. 读 [references/fields.md](references/fields.md) 和 [references/amap.md](references/amap.md)。
2. 确认 Web 服务 Key。没有就停，让用户把 Key 写进 `secrets/amap.env`。
3. 跑一键脚本：

```bash
python3 scripts/run_research.py \
  --city "昆山" \
  --industry "少儿编程,机器人教育" \
  --out-dir "/absolute/output/dir" \
  --env-file "/absolute/secrets/amap.env"
```

大城市加 `--expand-districts`。行业词不够时用 `--keywords "少儿编程,机器人教育,创客教育"`。
4. 打开 JSON，删掉打印店、餐饮、公寓等误伤；必要时改 P1/P2/P3。改完再跑：

```bash
python3 scripts/build_report.py --in-json raw.json --out report.docx
python3 scripts/build_map.py --in-json raw.json --out map.html
```
5. Word 用 documents skill 做完再给用户。地图让用户刷新已打开的 HTML；`file://` 搜附近失败时，用本地 `python3 -m http.server`。点一家店应出现店卡、可选半径虚线圈（100米/500米/1公里/3公里或自填），以及小区/学校/商场名称图钉。学校可按幼儿园、小学、初中、高中、其他筛选；也可在地图上自己落点看附近。

不要用官方 JS API。当前这把钥匙是 Web 服务 Key。不要把 Key 提交到 git。

## 脚本

| 文件 | 作用 |
| `scripts/run_research.py` | 检索 + 报告 + 地图 |
| `scripts/search_competitors.py` | 只检索，写出 JSON 和城市轮廓 |
| `scripts/build_report.py` | JSON -> Word |
| `scripts/build_map.py` | JSON -> 高德 HTML |
| `scripts/amap_common.py` | 读 Key、请求高德 |

## 验收

- 状态：每城都有 Word 和 HTML，名单只含在营
- 已验证：脚本能跑通；地图有轮廓和店点
- 未验证：点评条数、价格、班额（公开接口没有就标未查到）
- 已知风险：高德配额、误分类、`file://` 拦附近搜索
- 用户怎么确认：打开 Word 改黄底；打开地图点一家店，切 100 米 / 500 米看圈变小，小区/学校/商场 tab 有名称，小区有房价检索链接
