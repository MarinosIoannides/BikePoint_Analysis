"""
clean_data.py
--------------
This script takes the files that were not downloaded by API and cleans them and combines them to make sure they all align.
Takes spreadsheets from the raw_data folder
Outputs into the inputs folder for use in the model.

"""
import polars as pl

file_path = "data/"
# Data Cleaning
la_counts = pl.read_csv(file_path + "la_counts.csv")
deprivation_data = pl.read_csv(file_path + "deprivation.csv")

# Rename columns to make sense for graphs / joining
deprivation_data = deprivation_data.rename(
    {
        "Local Authority District name (2019)": "la_name",
        "Local Authority District code (2019)": "la_code",
        "Index of Multiple Deprivation (IMD) Rank": "rank",
        "Index of Multiple Deprivation (IMD) Decile": "decile",
        "LSOA code (2011)":"lsoa"
    }
)
# Make them numbers
deprivation_data = deprivation_data.with_columns(
    (pl.col("rank").str.replace(",", "")).cast(pl.Int64)
)
# With vs without bikepoints
deprivation_data = deprivation_data.with_columns(
    (pl.col("lsoa").is_in(la_counts["lsoa"])).alias("bikepoint")
)
# London only
deprivation_data = deprivation_data.with_columns(
    (pl.col("la_code").str.slice(0, 3) == "E09").alias("london")
)
# Bikepoints corelate with more deprived (lower score) LAs - both London and England-wid
# Childhood Obesity Data
children_data = pl.read_csv(file_path + "childhood_obesity.csv", infer_schema_length= 10000)
# I want the most recent data
children_data = children_data.filter(pl.col("Time period") == "2022/23")
# Don't want England-wide etc.
children_data = children_data.filter(pl.col("Area Type") == "Districts & UAs (from Apr 2023)")

children_data = children_data.rename({
    "Area Code":"la_code",
    "Area Name":"la_name"
})

overweight_children = children_data.filter(pl.col("Indicator Name") == "Reception prevalence of overweight (including obesity)")
obese_children = children_data.filter(pl.col("Indicator Name") == 'Reception prevalence of obesity (including severe obesity)')

overweight_children = overweight_children.rename({
    "Value": "5_yearolds_overweight"
})

obese_children = obese_children.rename({
    "Value": "5_yearolds_obese"
})
reception_children = obese_children.with_columns(
    pl.Series(overweight_children["5_yearolds_overweight"]).alias("5_yearolds_overweight")
)
# Join them together
la_bikepoints = deprivation_data.filter(pl.col("london") == True).group_by("la_name").mean()[["la_name", "bikepoint", "rank"]]
la_bikepoints = la_bikepoints.with_columns(
    (pl.col("bikepoint") != 0).alias("bikepoint_binary")
)
reception_children = reception_children[["la_name","5_yearolds_overweight", "5_yearolds_obese"]].join(la_bikepoints, on = "la_name")


overweight_children = children_data.filter(pl.col("Indicator Name") == "Year 6 prevalence of overweight (including obesity)")
obese_children = children_data.filter(pl.col("Indicator Name") == 'Year 6 prevalence of obesity (including severe obesity)')

overweight_children = overweight_children.rename({
    "Value": "11_yearolds_overweight"
})

obese_children = obese_children.rename({
    "Value": "11_yearolds_obese"
})
y6_children = obese_children.with_columns(
    pl.Series(overweight_children["11_yearolds_overweight"]).alias("11_yearolds_overweight")
)

full_children_df = reception_children.join(y6_children[["la_name", "11_yearolds_overweight", "11_yearolds_obese"]], on = "la_name")
# Adult Obesity Data
adult_obesity=  pl.read_csv(file_path + "adult_obesity.csv", infer_schema_length= 10000)
adult_obesity = adult_obesity.rename({
    "Area Code":"la_code",
    "Area Name":"la_name"
})
# Only want it at LA level
adult_obesity = adult_obesity.filter(pl.col("Area Type") == "Districts & UAs (2020/21)")
# I want the most recent data
today_adult_obesity = adult_obesity.filter(pl.col("Time period") == "2021/22")
historic_adult_obesity = adult_obesity.filter(pl.col("Time period") == "2015/16")



overweight_adult = today_adult_obesity.filter(pl.col("Indicator ID") == 93088)
obese_adult = today_adult_obesity.filter(pl.col("Indicator ID") == 93881)
historic_overweight_adult = historic_adult_obesity.filter(pl.col("Indicator ID") == 93088)
historic_obese_adult = historic_adult_obesity.filter(pl.col("Indicator ID") == 93881)

overweight_adult = overweight_adult.rename({
    "Value": "adults_overweight"
})

obese_adult = obese_adult.rename({
    "Value": "adults_obese"
})

historic_overweight_adult = historic_overweight_adult.rename({
    "Value": "historic_adults_overweight"
})

historic_obese_adult = historic_obese_adult.rename({
    "Value": "historic_adults_obese"
})

adults = obese_adult.with_columns(
    pl.Series(overweight_adult["adults_overweight"]).alias("adults_overweight")
)
adults = adults.with_columns(
    pl.Series(historic_overweight_adult["historic_adults_overweight"]).alias("historic_adults_overweight")
)
adults = adults.with_columns(
    pl.Series(historic_obese_adult["historic_adults_obese"]).alias("historic_adults_obese")
)
full_demographics_data = full_children_df.join(adults[["la_name","adults_overweight", "adults_obese", "historic_adults_overweight", "historic_adults_obese"]], on = "la_name")

full_demographics_data = full_demographics_data.with_columns(
    (pl.col("adults_overweight") - pl.col("historic_adults_overweight")).alias("overweight_change")
)
full_demographics_data = full_demographics_data.with_columns(
    (pl.col("adults_obese") - pl.col("historic_adults_obese")).alias("obese_change")
)
full_demographics_data.write_csv(file_path + "model_data.csv")