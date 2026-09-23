# city-competitor-research

Codex skill：输入行业和城市，生成在营竞品 Word 报告，以及可筛选、可搜附近小学的高德地图。

许可证：MIT。

## 你需要准备

1. 高德开放平台 **Web 服务** Key
2. Python 3，以及 `python-docx`

把 Key 写到 `secrets/amap.env`，不要提交这个文件：

```text
AMAP_MAPS_API_KEY=your_amap_web_service_key
```

## 运行

```bash
python3 scripts/run_research.py \
  --city "苏州" \
  --industry "少儿编程,机器人教育" \
  --out-dir "./out" \
  --env-file "./secrets/amap.env"
```

大城市可加 `--expand-districts`。

## 地图附近搜索

生成的 HTML 默认不内嵌 Key。本地可任选一种：

- 地址后加 `?key=你的Key`
- 浏览器控制台：`localStorage.AMAP_MAPS_API_KEY='你的Key'`
- 把 `examples/kunshan/amap-key.js.example` 复制为 `amap-key.js`

`file://` 打不开附近搜索时：

```bash
python3 -m http.server 8765 --directory examples/kunshan
```

## 昆山案例

见 [examples/kunshan](examples/kunshan/)。这是造物星球昆山在营业机构搜集的公开示例：一份可编辑 Word，一张高德交互地图。地图里没有 API Key。

## 口径

只收在营。没查到的价格、班额、点评条数写「未查到」，不编造。字段说明见 `references/fields.md`。
