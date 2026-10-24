# Geographic / transport proper-noun sources

本層只在建置詞庫時使用；執行中的輸入法仍只 mmap `dictionary.bin`，不會另外把這些 CSV 全部載入記憶體。

## 行政區與國家／地區

- `taiwan_admin_divisions.csv`：22 縣市、368 鄉鎮市區。名稱依台灣現行行政區名稱整理；可由內政部國土測繪中心「代碼服務－鄉鎮市區清單」核對。
- `common_country_region_names.csv`：常用國家／地區中文名稱與常見別稱，採台灣常用譯名，並參考中華郵政「國外郵政國名/地區名中英文對照表」。

## 道路主名稱

- `taiwan_road_main_names.csv`：17,565 個去重複道路主名稱。
- 明確不收「一段／二段／…」等段號；來源中仍把段號嵌在側街名稱內的項目也會排除。
- 僅保留以「路／街／大道」結尾的主名稱；不收巷、弄、門牌。
- 本版正規化快照來自 `donma/TaiwanAddressCityAreaRoadChineseEnglishJSON` 的 `AllData.json`，blob SHA `3e42da0c6cf128df35241277d747318dd841db61`；該資料集參考中華郵政地址資料，專案 README 標示 MIT License（Copyright (c) 2016 Donma）。
- 官方核對來源：政府資料開放平台「全國路名資料」（內政部戶政司，dataset 35321）。

## 車站／捷運／輕軌

- `taiwan_transit_stations.csv`：543 個「系統 × 站名」去重複列，涵蓋台鐵、高鐵、阿里山林鐵、台北捷運、桃園機場捷運、台中捷運、高雄捷運／輕軌、新北捷運（淡海、安坑、三鶯等）。
- 本版站名快照由 `siriushsu/taiwan-rail-live` 的 `data/track_stations.geojson` 只抽取 `sys` 與 `name`（不攜帶座標、軌道幾何或程式碼），blob SHA `eaef7fc1813fe753e1800d614235169d933b344a`。該專案資料檔說明其來源包含交通部 TDX、台鐵官方公開資料等第三方公開資料；本專案只使用站名事實資料並保留此來源說明。
- 產生詞庫時會加入常用「站／車站」以及 `臺鐵／高鐵／捷運／輕軌／機捷` 前綴別名；括號或斜線名稱拆成可用注音輸入的漢字別名，避免把數字／符號硬塞進注音音節。

## 機場

- `taiwan_airports.csv`：交通部民用航空局「機場分佈圖」列出的 17 座機場，另加台灣常用別稱（桃園機場、桃機、松山機場、小港機場、清泉崗機場、馬公機場、尚義機場等）。
- 官方來源：交通部民用航空局「機場分佈圖」與「各機場服務臺電話」。

## 產生方式

- `build_transport_source_lists.py`：把外部道路 JSON／車站 GeoJSON 正規化成小型 CSV；本工具本身不連網，方便日後更新時重現同一套規則。
- `build_geographic_words.py`：依 bundled dictionary 的單字讀音，加上少量台灣地名／罕用道路字讀音覆寫，產生 `geographic_words.csv`。
- `inject_dictionary_words.py`：把產生結果注入 ZYDICT2。

所有執行期地名／道路／車站／機場查詢皆完全離線；安裝後不需要網路查詢。
