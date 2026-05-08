from pyspark.sql import SparkSession
from pyspark.sql.functions import col, coalesce, count, lit, month, sum as spark_sum, year


def build_spark(app_name: str = "DisasterAnalytics"):
    return (
        SparkSession.builder.appName(app_name)
        .master("spark://spark-master:7077")
        .getOrCreate()
    )


def read_dataset(spark: SparkSession, csv_path: str):
    df = spark.read.option("header", True).option("multiLine", True).csv(csv_path)
    return (
        df.withColumn("DirectEconomicLosses", coalesce(col("DirectEconomicLosses").cast("double"), lit(0.0)))
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


def event_classify_distribution(df):
    rows = (
        df.groupBy("EventClassify")
        .agg(count("*").alias("value"))
        .orderBy(col("value").desc())
        .collect()
    )
    return [{"name": r["EventClassify"] or "未知", "value": int(r["value"])} for r in rows]


def year_trend(df):
    rows = (
        df.groupBy("event_year")
        .agg(
            spark_sum("DeathsNumber").alias("deaths"),
            spark_sum("AffectedPopulation").alias("affected"),
            spark_sum("DirectEconomicLosses").alias("loss"),
        )
        .orderBy("event_year")
        .collect()
    )
    return [
        {
            "year": int(r["event_year"]) if r["event_year"] else 0,
            "deaths": float(r["deaths"] or 0),
            "affected": float(r["affected"] or 0),
            "loss": float(r["loss"] or 0),
        }
        for r in rows
    ]
