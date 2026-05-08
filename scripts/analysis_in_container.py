from pathlib import Path
import json

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, coalesce, count, lit, month, sum as spark_sum, year

spark = SparkSession.builder.appName("DisasterAnalytics").master("spark://spark-master:7077").getOrCreate()

df = (
    spark.read.option("header", True)
    .csv("hdfs://hadoop-namenode:9000/data/disaster/disaster_2016_2020_province_aligned.csv")
    .withColumn("DirectEconomicLosses", coalesce(col("DirectEconomicLosses").cast("double"), lit(0.0)))
    .withColumn("DeathsNumber", coalesce(col("DeathsNumber").cast("double"), lit(0.0)))
    .withColumn("AffectedPopulation", coalesce(col("AffectedPopulation").cast("double"), lit(0.0)))
    .withColumn("CropsAffectedArea", coalesce(col("CropsAffectedArea").cast("double"), lit(0.0)))
    .withColumn("HouseCollapse", coalesce(col("HouseCollapse").cast("double"), lit(0.0)))
    .withColumn("SeriousDamage", coalesce(col("SeriousDamage").cast("double"), lit(0.0)))
    .withColumn("SecondaryDamage", coalesce(col("SecondaryDamage").cast("double"), lit(0.0)))
    .withColumn("MinorDamage", coalesce(col("MinorDamage").cast("double"), lit(0.0)))
    .withColumn("event_year", year(col("DeclareDate")))
    .withColumn("event_month", month(col("DeclareDate")))
)

kpi = {
    "totalEvents": int(df.count()),
    "totalDeaths": int(df.agg(spark_sum("DeathsNumber").alias("x")).first()["x"] or 0),
    "totalLossWanYuan": float(df.agg(spark_sum("DirectEconomicLosses").alias("x")).first()["x"] or 0),
    "totalAffected": int(df.agg(spark_sum("AffectedPopulation").alias("x")).first()["x"] or 0),
}

event_classify = [
    {"name": r["EventClassify"] or "未知", "value": int(r["value"])}
    for r in df.groupBy("EventClassify").agg(count("*").alias("value")).orderBy(col("value").desc()).collect()
]
province_heat = [
    {"name": r["ProvinceNorm"] or "未知", "value": float(r["loss"] or 0)}
    for r in df.groupBy("ProvinceNorm").agg(spark_sum("DirectEconomicLosses").alias("loss")).orderBy(col("loss").desc()).collect()
]
year_trend = [
    {
        "year": int(r["event_year"]) if r["event_year"] else 0,
        "deaths": float(r["deaths"] or 0),
        "affected": float(r["affected"] or 0),
        "loss": float(r["loss"] or 0),
    }
    for r in df.groupBy("event_year")
    .agg(
        spark_sum("DeathsNumber").alias("deaths"),
        spark_sum("AffectedPopulation").alias("affected"),
        spark_sum("DirectEconomicLosses").alias("loss"),
    )
    .orderBy("event_year")
    .collect()
]
loss_top10 = province_heat[:10]
month_heat = [
    {"month": int(r["event_month"] or 0), "count": int(r["cnt"])}
    for r in df.groupBy("event_month").agg(count("*").alias("cnt")).orderBy("event_month").collect()
]
population_vs_loss = [
    {"name": r["EventClassify"] or "未知", "affected": float(r["affected"] or 0), "loss": float(r["loss"] or 0)}
    for r in df.groupBy("EventClassify")
    .agg(
        spark_sum("AffectedPopulation").alias("affected"),
        spark_sum("DirectEconomicLosses").alias("loss"),
    )
    .collect()
]
house_damage_stack = [
    {
        "year": int(r["event_year"]) if r["event_year"] else 0,
        "collapse": float(r["collapse"] or 0),
        "serious": float(r["serious"] or 0),
        "secondary": float(r["secondary"] or 0),
        "minor": float(r["minor"] or 0),
    }
    for r in df.groupBy("event_year")
    .agg(
        spark_sum("HouseCollapse").alias("collapse"),
        spark_sum("SeriousDamage").alias("serious"),
        spark_sum("SecondaryDamage").alias("secondary"),
        spark_sum("MinorDamage").alias("minor"),
    )
    .orderBy("event_year")
    .collect()
]
crop_trend = [
    {"year": int(r["event_year"]) if r["event_year"] else 0, "value": float(r["crop"] or 0)}
    for r in df.groupBy("event_year").agg(spark_sum("CropsAffectedArea").alias("crop")).orderBy("event_year").collect()
]
casualty_rose = [
    {"name": r["ProvinceNorm"] or "未知", "value": float(r["death"] or 0)}
    for r in df.groupBy("ProvinceNorm")
    .agg(spark_sum("DeathsNumber").alias("death"))
    .orderBy(col("death").desc())
    .limit(12)
    .collect()
]

output = {
    "kpi": kpi,
    "charts": {
        "eventClassify": event_classify,
        "provinceHeat": province_heat,
        "yearTrend": year_trend,
        "lossTop10": loss_top10,
        "monthHeat": month_heat,
        "populationVsLoss": population_vs_loss,
        "houseDamageStack": house_damage_stack,
        "cropTrend": crop_trend,
        "casualtyRose": casualty_rose,
    },
}

out = Path("/home/jovyan/work/analysis_output.json")
out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"written: {out}")
spark.stop()
