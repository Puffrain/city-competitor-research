# 高德用法

必须用 **Web 服务** Key，不要用 JS API Key。官方 JS API 不能用 Web 服务钥匙。

## Key 放哪里

按这个顺序读：

1. 环境变量 `AMAP_MAPS_API_KEY`
2. `--env-file`
3. 当前项目 `secrets/amap.env`
4. 当前项目 `amap.env`

不要把 Key 写进 Git、Word、聊天记录。地图 HTML 默认不内嵌 Key；附近搜索会读 `?key=`、`localStorage.AMAP_MAPS_API_KEY` 或同目录 `amap-key.js`。

## 用到的接口

- `/v3/place/text`：按城市和关键词搜店
- `/v3/place/around`：地图页搜附近小学、小区
- `/v3/config/district`：城市区划和轮廓

坐标按 GCJ-02，和高德瓦片一致。

## 配额与打开方式

`file://` 打开地图时，附近搜索可能被浏览器拦住。失败就用本地 HTTP：

```bash
python3 -m http.server 8765 --directory "<输出目录>"
```

然后打开对应 HTML。
