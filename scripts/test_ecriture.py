from session import get_spark

spark = get_spark()
spark.range(5).write.mode("overwrite").parquet("data/tmp_test")
print("lignes relues :", spark.read.parquet("data/tmp_test").count())