import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["metrics"])
CSV_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "csv" / "disaster_2016_2020.csv"

PROVINCES = [
    "北京市",
    "天津市",
    "上海市",
    "重庆市",
    "河北省",
    "山西省",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "江苏省",
    "浙江省",
    "安徽省",
    "福建省",
    "江西省",
    "山东省",
    "河南省",
    "湖北省",
    "湖南省",
    "广东省",
    "海南省",
    "四川省",
    "贵州省",
    "云南省",
    "陕西省",
    "甘肃省",
    "青海省",
    "内蒙古自治区",
    "广西壮族自治区",
    "西藏自治区",
    "宁夏回族自治区",
    "新疆维吾尔自治区",
]

REGION_ALIAS = {
    "北京": "北京市",
    "天津": "天津市",
    "上海": "上海市",
    "重庆": "重庆市",
    "河北": "河北省",
    "山西": "山西省",
    "辽宁": "辽宁省",
    "吉林": "吉林省",
    "黑龙江": "黑龙江省",
    "江苏": "江苏省",
    "浙江": "浙江省",
    "安徽": "安徽省",
    "福建": "福建省",
    "江西": "江西省",
    "山东": "山东省",
    "河南": "河南省",
    "湖北": "湖北省",
    "湖南": "湖南省",
    "广东": "广东省",
    "海南": "海南省",
    "四川": "四川省",
    "贵州": "贵州省",
    "云南": "云南省",
    "陕西": "陕西省",
    "甘肃": "甘肃省",
    "青海": "青海省",
    "内蒙古": "内蒙古自治区",
    "广西": "广西壮族自治区",
    "西藏": "西藏自治区",
    "宁夏": "宁夏回族自治区",
    "新疆": "新疆维吾尔自治区",
}


@lru_cache(maxsize=1)
def load_df():
    if not CSV_FILE.exists():
        raise HTTPException(status_code=404, detail="灾害 CSV 不存在，请先执行 scripts/init_hdfs.py")
    df = pd.read_csv(CSV_FILE)
    num_cols = [
        "DirectEconomicLosses",
        "DeathsNumber",
        "AffectedPopulation",
        "CropsAffectedArea",
        "HouseCollapse",
        "SeriousDamage",
        "SecondaryDamage",
        "MinorDamage",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["DeclareDate"] = pd.to_datetime(df.get("DeclareDate"), errors="coerce")
    df["event_year"] = df["DeclareDate"].dt.year
    df["event_month"] = df["DeclareDate"].dt.month
    return df


def _to_region(token: str):
    t = str(token or "").strip()
    if not t:
        return None
    if t in PROVINCES:
        return t
    if t in REGION_ALIAS:
        return REGION_ALIAS[t]
    for p in PROVINCES:
        if p in t:
            return p
    for alias, p in REGION_ALIAS.items():
        if alias in t:
            return p
    return None


def _extract_regions(raw: str):
    text = str(raw or "")
    if not text:
        return []
    parts = re.split(r"[，,、/；;|\s]+", text)
    regions = []
    for part in parts:
        r = _to_region(part)
        if r and r not in regions:
            regions.append(r)
    if not regions:
        for p in PROVINCES:
            if p in text and p not in regions:
                regions.append(p)
        for alias, p in REGION_ALIAS.items():
            if alias in text and p not in regions:
                regions.append(p)
    return regions


def _extract_cities(raw: str):
    text = str(raw or "").strip()
    if not text:
        return []
    parts = re.split(r"[，,、/；;|\s]+", text)
    cities = []
    for part in parts:
        token = str(part or "").strip()
        if not token:
            continue
        matched = re.findall(r"[\u4e00-\u9fa5]{2,10}?(?:市|州|地区|盟|县)", token)
        for m in matched:
            if m not in cities:
                cities.append(m)
        if matched:
            continue
        if re.search(r"(市|州|地区|盟|县)$", token):
            if token not in cities:
                cities.append(token)
    return cities


@lru_cache(maxsize=1)
def load_region_df():
    df = load_df().copy()
    region_lists = []
    for row in df.itertuples(index=False):
        prov = _extract_regions(getattr(row, "Province", ""))
        region_lists.append(prov)
    df["region_list"] = region_lists
    exploded = df.explode("region_list")
    exploded = exploded[exploded["region_list"].notna()]
    exploded["ProvinceNorm"] = exploded["region_list"].astype(str)
    exploded = exploded[exploded["ProvinceNorm"].isin(PROVINCES)]
    return exploded


def _available_regions():
    present = set(load_region_df()["ProvinceNorm"].dropna().unique().tolist())
    return [p for p in PROVINCES if p in present]


def _resolve_region(query: str, all_regions: list[str]):
    q = str(query or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="region 不能为空")
    if q == "全国":
        return "全国", []
    direct = _to_region(q)
    if direct in all_regions:
        return direct, []

    contains = [r for r in all_regions if q in r or r in q]
    if contains:
        return contains[0], contains[:5]

    scored = sorted(
        [(r, SequenceMatcher(None, q, r).ratio()) for r in all_regions],
        key=lambda x: x[1],
        reverse=True,
    )
    if not scored or scored[0][1] < 0.35:
        raise HTTPException(status_code=404, detail=f"未找到与“{query}”相近的省级地区")
    return scored[0][0], [i[0] for i in scored[:5]]


def _suggestions_by_type(event_type: str):
    farmer = {
        "洪涝": ["提前疏通田间沟渠并备好抽水设备", "低洼地块优先改种耐涝作物", "降雨高峰前完成农资与饲料转移"],
        "台风": ["加固大棚与畜舍，提前采收成熟作物", "渔业养殖区提前回港避风", "准备断电应急与保温设施"],
        "雪灾": ["大棚提前加固和覆膜保温", "果树做好防冻包扎", "储备饲草并检查饮水防冻"],
    }.get(event_type, ["关注短临预报，提前安排播种和收获窗口", "对高风险地块执行分区管理", "提前备足应急农资和排涝物资"])
    enterprise = {
        "洪涝": ["工厂低洼区设置防倒灌挡板", "关键设备上移并做好防水绝缘", "物流仓储采用分仓备份和绕行路线"],
        "台风": ["停工停产预案按红橙黄分级触发", "户外作业提前撤离", "供应链关键节点准备双来源替代"],
        "地震": ["重点厂房开展抗震鉴定", "危化品仓库加固与泄漏应急演练", "核心业务建立异地容灾"],
    }.get(event_type, ["完善业务连续性计划（BCP）", "关键数据和电力系统做冗余备份", "按风险等级分层停工和复工"])
    government = {
        "洪涝": ["对易涝片区执行网格化巡查", "提前开放临时避险点并发布转移指令", "部门联动更新排涝泵站值守计划"],
        "台风": ["海陆空交通执行联动管制预案", "高风险工地和景区提前停业", "强化多渠道预警覆盖到村到户"],
        "地震": ["重点公共建筑实施快速安全评估", "应急救援力量前置部署", "学校医院开展高频疏散演练"],
    }.get(event_type, ["建立“气象+应急+行业”联合会商机制", "提升乡镇到社区的预警触达率", "重点人群执行分级转移和保障"])
    return {"farmers": farmer, "enterprise": enterprise, "government": government}


def _build_from_df(df: pd.DataFrame, region_name: str, matched_fuzzy=False, alternatives=None):
    alternatives = alternatives or []
    if df.empty:
        raise HTTPException(status_code=404, detail=f"未找到地区: {region_name}")

    year = (
        df.groupby("event_year", dropna=True)
        .agg(
            deaths=("DeathsNumber", "sum"),
            affected=("AffectedPopulation", "sum"),
            loss=("DirectEconomicLosses", "sum"),
            crop=("CropsAffectedArea", "sum"),
            collapse=("HouseCollapse", "sum"),
            serious=("SeriousDamage", "sum"),
            secondary=("SecondaryDamage", "sum"),
            minor=("MinorDamage", "sum"),
            events=("EventClassify", "count"),
        )
        .reset_index()
        .sort_values("event_year")
    )
    year_trend = [
        {"year": int(i.event_year) if pd.notna(i.event_year) else 0, "deaths": float(i.deaths), "affected": float(i.affected), "loss": float(i.loss)}
        for i in year.itertuples(index=False)
    ]
    crop_trend = [{"year": int(i.event_year), "value": float(i.crop)} for i in year.itertuples(index=False)]
    house_damage_stack = [
        {"year": int(i.event_year), "collapse": float(i.collapse), "serious": float(i.serious), "secondary": float(i.secondary), "minor": float(i.minor)}
        for i in year.itertuples(index=False)
    ]
    month = df.groupby("event_month", dropna=True)["EventClassify"].count().reset_index(name="count").sort_values("event_month")
    month_heat = [{"month": int(i.event_month), "count": int(i.count)} for i in month.itertuples(index=False)]

    type_dist = (
        df.groupby("EventClassify", dropna=True)
        .agg(value=("EventClassify", "count"), affected=("AffectedPopulation", "sum"), loss=("DirectEconomicLosses", "sum"))
        .reset_index()
        .sort_values("value", ascending=False)
    )
    top_type = str(type_dist.iloc[0]["EventClassify"]) if not type_dist.empty else "未知"
    population_vs_loss = [{"name": str(i.EventClassify), "affected": float(i.affected), "loss": float(i.loss)} for i in type_dist.itertuples(index=False)]

    if region_name == "全国":
        rose_group = (
            df.groupby("ProvinceNorm", dropna=True)["DeathsNumber"]
            .sum()
            .reindex(PROVINCES, fill_value=0.0)
            .reset_index(name="value")
        )
        casualty_rose = rose_group.sort_values("value", ascending=False)
        casualty_rose = [{"name": str(i.ProvinceNorm), "value": float(i.value)} for i in casualty_rose.itertuples(index=False)]
    else:
        city_df = df.copy()
        city_df["city_list"] = city_df.get("City", "").apply(_extract_cities)
        city_df = city_df.explode("city_list")
        city_df = city_df[city_df["city_list"].notna()]
        city_df["CityNorm"] = city_df["city_list"].astype(str).str.strip()
        city_df = city_df[city_df["CityNorm"] != ""]
        if city_df.empty:
            casualty_rose = [{"name": region_name, "value": float(df["DeathsNumber"].sum())}]
        else:
            rose_group = city_df.groupby("CityNorm", dropna=True)["DeathsNumber"].sum().reset_index(name="value")
            casualty_rose = rose_group.sort_values("value", ascending=False)
            casualty_rose = [{"name": str(i.CityNorm), "value": float(i.value)} for i in casualty_rose.itertuples(index=False)]

    current_year = int(df["event_year"].dropna().max()) if not df["event_year"].dropna().empty else 2020
    weighted = df.copy()
    weighted["weight"] = weighted["event_year"].fillna(current_year).apply(lambda y: 1.0 + max(0.0, (float(y) - (current_year - 4)) * 0.22))
    probs = weighted.groupby("EventClassify", dropna=True)["weight"].sum().reset_index(name="score").sort_values("score", ascending=False)
    total_score = float(probs["score"].sum()) if not probs.empty else 0.0
    type_probability = [
        {"type": str(i.EventClassify), "probability": round((float(i.score) / total_score) * 100, 2) if total_score > 0 else 0.0}
        for i in probs.itertuples(index=False)
    ]

    events_per_year = year["events"].tolist()
    if events_per_year:
        latest = events_per_year[-1]
        avg = sum(events_per_year) / len(events_per_year)
        probability = max(8, min(95, int((latest / avg) * 52 if avg > 0 else 25)))
    else:
        probability = 20

    overview = {
        "region": region_name,
        "matchedByFuzzy": matched_fuzzy,
        "alternatives": alternatives,
        "totalEvents": int(len(df)),
        "totalDeaths": int(df["DeathsNumber"].sum()),
        "totalLossWanYuan": float(df["DirectEconomicLosses"].sum()),
        "totalAffected": int(df["AffectedPopulation"].sum()),
    }
    prediction = {
        "nextYearRiskProbability": probability,
        "nextYearLikelyType": top_type,
        "typeProbabilityTop": type_probability[:8],
        "basis": "基于2016-2020该地区历史灾害频次、损失强度与类型占比的统计预测",
    }

    return {
        "kpi": {
            "totalEvents": overview["totalEvents"],
            "totalDeaths": overview["totalDeaths"],
            "totalLossWanYuan": overview["totalLossWanYuan"],
            "totalAffected": overview["totalAffected"],
        },
        "overview": overview,
        "prediction": prediction,
        "recommendations": _suggestions_by_type(top_type),
        "charts": {
            "eventClassify": [{"name": str(i.EventClassify), "value": int(i.value)} for i in type_dist.itertuples(index=False)],
            "provinceHeat": [
                {"name": str(i.ProvinceNorm), "value": float(i.loss)}
                for i in df.groupby("ProvinceNorm", dropna=True)["DirectEconomicLosses"]
                .sum()
                .reset_index(name="loss")
                .sort_values("loss", ascending=False)
                .itertuples(index=False)
            ],
            "yearTrend": year_trend,
            "lossTop10": [
                {"name": str(i.ProvinceNorm), "value": float(i.loss)}
                for i in df.groupby("ProvinceNorm", dropna=True)["DirectEconomicLosses"]
                .sum()
                .reset_index(name="loss")
                .sort_values("loss", ascending=False)
                .head(10)
                .itertuples(index=False)
            ],
            "monthHeat": month_heat,
            "populationVsLoss": population_vs_loss,
            "houseDamageStack": house_damage_stack,
            "cropTrend": crop_trend,
            "casualtyRose": casualty_rose,
            "typeProbability": type_probability,
        },
    }


def _build_region_result(region: str):
    df = load_region_df()
    all_regions = _available_regions()
    query = str(region or "").strip()
    resolved, alternatives = _resolve_region(query, all_regions)
    if resolved == "全国":
        return _build_from_df(df, "全国", matched_fuzzy=False, alternatives=[])
    sub = df[df["ProvinceNorm"] == resolved].copy()
    return _build_from_df(sub, resolved, matched_fuzzy=(resolved != query), alternatives=alternatives)


@router.get("/kpi")
def get_kpi():
    return _build_region_result("全国").get("kpi", {})


@router.get("/chart/{chart_key}")
def get_chart(chart_key: str):
    charts = _build_region_result("全国").get("charts", {})
    if chart_key not in charts:
        raise HTTPException(status_code=404, detail=f"图表 {chart_key} 不存在")
    return charts[chart_key]


@router.get("/all")
def get_all():
    base = _build_region_result("全国")
    return {"kpi": base["kpi"], "charts": base["charts"]}


@router.get("/regions")
def get_regions():
    return {"regions": ["全国"] + _available_regions()}


@router.get("/region-insight")
def get_region_insight(region: str):
    return _build_region_result(region)
