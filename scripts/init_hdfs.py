from pathlib import Path
import subprocess
import re

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
CSV_DIR = DATA_DIR / "csv"

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


def normalize_year_file(xlsx_path: Path):
    year = xlsx_path.stem[:4]
    df = pd.read_excel(xlsx_path, sheet_name=0)
    # 清理每个文件第一行的中文字段说明行
    if len(df) > 0 and str(df.iloc[0].get("EventClassify", "")).strip() == "事件分类":
        df = df.iloc[1:].copy()
    df["Year"] = int(year)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    out = CSV_DIR / f"{year}.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def _extract_regions(raw: str):
    text = str(raw or "")
    if not text:
        return []
    parts = re.split(r"[，,、/；;|\s]+", text)
    regions = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p in PROVINCES:
            reg = p
        elif p in REGION_ALIAS:
            reg = REGION_ALIAS[p]
        else:
            reg = None
            for std in PROVINCES:
                if std in p:
                    reg = std
                    break
            if not reg:
                for alias, std in REGION_ALIAS.items():
                    if alias in p:
                        reg = std
                        break
        if reg and reg not in regions:
            regions.append(reg)
    if not regions:
        for std in PROVINCES:
            if std in text and std not in regions:
                regions.append(std)
        for alias, std in REGION_ALIAS.items():
            if alias in text and std not in regions:
                regions.append(std)
    return regions


def build_aligned_csv(merged: pd.DataFrame):
    rows = []
    for _, row in merged.iterrows():
        regions = _extract_regions(row.get("Province", ""))
        if not regions:
            continue
        for reg in regions:
            rec = row.copy()
            rec["ProvinceNorm"] = reg
            rows.append(rec)
    aligned = pd.DataFrame(rows)
    out = CSV_DIR / "disaster_2016_2020_province_aligned.csv"
    aligned.to_csv(out, index=False, encoding="utf-8-sig")
    return out, len(aligned)


def main():
    files = sorted(DATA_DIR.glob("*.xlsx"))
    if not files:
        raise SystemExit("未在 data 目录找到 xlsx 文件")

    csv_files = [normalize_year_file(f) for f in files]
    merged = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
    merged_file = CSV_DIR / "disaster_2016_2020.csv"
    merged.to_csv(merged_file, index=False, encoding="utf-8-sig")
    print(f"CSV 已生成: {merged_file}")
    aligned_file, aligned_rows = build_aligned_csv(merged)
    print(f"省级对齐CSV已生成: {aligned_file} (rows={aligned_rows})")

    print("\n尝试自动上传 HDFS...")
    try:
        subprocess.run(
            ["docker", "exec", "hadoop-namenode", "hdfs", "dfs", "-mkdir", "-p", "/data/disaster"],
            check=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                "hadoop-namenode",
                "hdfs",
                "dfs",
                "-put",
                "-f",
                "/data/csv/disaster_2016_2020.csv",
                "/data/disaster/",
            ],
            check=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                "hadoop-namenode",
                "hdfs",
                "dfs",
                "-put",
                "-f",
                "/data/csv/disaster_2016_2020_province_aligned.csv",
                "/data/disaster/",
            ],
            check=True,
        )
        print("HDFS 上传成功: /data/disaster/disaster_2016_2020.csv")
        print("HDFS 上传成功: /data/disaster/disaster_2016_2020_province_aligned.csv")
    except Exception as exc:
        print(f"自动上传失败: {exc}")
        print("请手动执行:")
        print("docker exec hadoop-namenode hdfs dfs -mkdir -p /data/disaster")
        print(
            "docker exec hadoop-namenode hdfs dfs -put -f /data/csv/disaster_2016_2020.csv /data/disaster/"
        )
        print(
            "docker exec hadoop-namenode hdfs dfs -put -f /data/csv/disaster_2016_2020_province_aligned.csv /data/disaster/"
        )


if __name__ == "__main__":
    main()
