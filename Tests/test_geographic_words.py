#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Shared" / "Tools"))

from build_geographic_words import (
    build_words,
    load_admin,
    load_airports,
    load_countries,
    load_road_names,
    load_stations,
)
from repair_dictionary_taiwan import read_dictionary

RES = ROOT / "Shared" / "Resources"
ADMIN = RES / "taiwan_admin_divisions.csv"
COUNTRIES = RES / "common_country_region_names.csv"
ROADS = RES / "taiwan_road_main_names.csv"
STATIONS = RES / "taiwan_transit_stations.csv"
AIRPORTS = RES / "taiwan_airports.csv"
DICT = RES / "dictionary.bin"

admin = load_admin(ADMIN)
assert len(admin) == 368
assert len({c for c, _ in admin}) == 22
assert ("苗栗縣", "南庄鄉") in admin
assert ("臺中市", "西屯區") in admin
assert ("臺東縣", "蘭嶼鄉") in admin
assert ("連江縣", "東引鄉") in admin

countries = load_countries(COUNTRIES)
assert len(countries) >= 150
for name in ["臺灣", "日本", "韓國", "美國", "加拿大", "英國", "法國", "德國", "冰島", "烏克蘭", "澳洲", "紐西蘭"]:
    assert name in countries, name

roads = load_road_names(ROADS)
assert len(roads) == 17_565
assert len(set(roads)) == len(roads)
assert not any(re.search(r"[0-9０-９零〇一二三四五六七八九十百]+段", x) for x in roads)
for name in ["忠孝東路", "中山路", "凱達格蘭大道", "臺灣大道", "一廍路", "鮕鮘坑街"]:
    assert name in roads, name

stations = load_stations(STATIONS)
assert len(stations) == 543
systems = {s for s, _ in stations}
for system in ["tra_sched", "thsr_sched", "afr_sched", "mrt", "tymc", "tmrt", "krtc", "ntdlrt", "ntalrt", "sanying"]:
    assert system in systems, system
for pair in [
    ("tra_sched", "臺北"),
    ("thsr_sched", "左營"),
    ("mrt", "台北車站"),
    ("tymc", "機場第一航廈站"),
    ("tmrt", "大慶"),
]:
    assert pair in stations, pair

airports = load_airports(AIRPORTS)
official_airports = {name for name, kind in airports if kind == "official"}
assert len(official_airports) == 17
for name in ["臺灣桃園國際機場", "臺北松山國際機場", "高雄國際機場", "臺中國際機場", "金門機場", "七美機場"]:
    assert name in official_airports, name

words = build_words(DICT, ADMIN, COUNTRIES, ROADS, STATIONS, AIRPORTS)
expected = set(words.keys())
entries, _ = read_dictionary(DICT)
actual = {(e.word, e.pron) for e in entries}
missing = expected - actual
assert not missing, f"bundled dictionary is missing {len(missing)} generated geographic/transport entries; first={next(iter(missing), None)!r}"

critical = {
    "三重": ("ㄙㄢ", "ㄔㄨㄥˊ"),
    "埔里": ("ㄆㄨˇ", "ㄌㄧˇ"),
    "朴子": ("ㄆㄨˊ", "ㄗˇ"),
    "茄萣": ("ㄑㄧㄝˊ", "ㄉㄧㄥˋ"),
    "三地門": ("ㄙㄢ", "ㄉㄧˋ", "ㄇㄣˊ"),
    "苗栗縣南庄鄉": ("ㄇㄧㄠˊ", "ㄌㄧˋ", "ㄒㄧㄢˋ", "ㄋㄢˊ", "ㄓㄨㄤ", "ㄒㄧㄤ"),
    "美國": ("ㄇㄟˇ", "ㄍㄨㄛˊ"),
    "冰島": ("ㄅㄧㄥ", "ㄉㄠˇ"),
    "忠孝東路": ("ㄓㄨㄥ", "ㄒㄧㄠˋ", "ㄉㄨㄥ", "ㄌㄨˋ"),
    "臺灣大道": ("ㄊㄞˊ", "ㄨㄢ", "ㄉㄚˋ", "ㄉㄠˋ"),
    "一廍路": ("ㄧ", "ㄅㄨˋ", "ㄌㄨˋ"),
    "鮕鮘坑街": ("ㄍㄨ", "ㄉㄞˋ", "ㄎㄥ", "ㄐㄧㄝ"),
    "臺北車站": ("ㄊㄞˊ", "ㄅㄟˇ", "ㄔㄜ", "ㄓㄢˋ"),
    "高鐵左營站": ("ㄍㄠ", "ㄊㄧㄝˇ", "ㄗㄨㄛˇ", "ㄧㄥˊ", "ㄓㄢˋ"),
    "捷運淡水站": ("ㄐㄧㄝˊ", "ㄩㄣˋ", "ㄉㄢˋ", "ㄕㄨㄟˇ", "ㄓㄢˋ"),
    "臺灣桃園國際機場": ("ㄊㄞˊ", "ㄨㄢ", "ㄊㄠˊ", "ㄩㄢˊ", "ㄍㄨㄛˊ", "ㄐㄧˋ", "ㄐㄧ", "ㄔㄤˇ"),
    "桃園機場": ("ㄊㄠˊ", "ㄩㄢˊ", "ㄐㄧ", "ㄔㄤˇ"),
}
for word, pron in critical.items():
    assert (word, pron) in actual, (word, pron)

# Regression: the transport expansion must not drop existing polyphonic readings.
assert ("期", ("ㄑㄧˊ",)) in actual

print(
    "test_geographic_words: OK "
    f"(22 counties/cities, 368 districts, {len(countries)} country/region names, "
    f"{len(roads)} road main names, {len(stations)} station rows, 17 official airports, "
    f"{len(words)} generated entries)"
)
