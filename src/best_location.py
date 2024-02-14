import pandas as pd
import re
import os
import glob


def find_csv_files(directory):
    # Change the directory
    os.chdir(directory)
    # Find all CSV files
    csv_files = glob.glob("*.csv")
    return csv_files


def find_country_code(nuts_str):
    pattern = r"[A-Z]{2}"
    matches = re.findall(pattern, nuts_str)
    return matches[0]


def make_nuts2_dict():
    with open("eurodata/nuts.txt") as f:
        lines = f.readlines()
        nuts2_dict = {}
        for line in lines:
            line_lst = line.strip().split(" ")
            nuts2_dict[line_lst[0]] = " ".join(line_lst[1:])
        return nuts2_dict


def clean_df(directory, file_name, year, nuts2=True):
    df = pd.read_csv(f"{directory}/{file_name}")
    df = df[df["TIME_PERIOD"] == year]
    df = df[(~df["geo"].str.contains("EA")) | (~df["geo"].str.contains("EU"))]
    if nuts2:
        df = df[df["geo"].str.len() > 3]
    df = df[["geo", "OBS_VALUE"]]
    df["country"] = df["geo"].apply(find_country_code)
    df = df.rename(columns={"OBS_VALUE": f"{file_name}"})
    if not nuts2:
        df.drop(["geo"], axis=1, inplace=True)
    return df


def main():
    directory = "eurodata"
    file_dict = {
        "Net_occupancy_rate.csv": [True, 2021],
        "expenditure_accomodation.csv": [False, 2021],
        "Arrivals_accommodation.csv": [True, 2021],
        "expenditure_per_trip_avg.csv": [False, 2021],
        "hicp_per_country.csv": [False, "2023-12"],
    }
    df = clean_df(directory, "num_of_accoms.csv", 2021)

    for key, value in file_dict.items():
        temp_df = clean_df(directory, key, value[1], nuts2=value[0])
        if value[0]:
            df = df.merge(temp_df, how="left", on=["geo", "country"])
        elif not value[0]:
            df = df.merge(temp_df, how="left", on="country")

    object_columns = df.select_dtypes(include=["object"]).columns

    df.loc[
        :,
        ~df.columns.isin(object_columns),
    ] = (
        df.loc[
            :,
            ~df.columns.isin(object_columns),
        ]
        - df.loc[
            :,
            ~df.columns.isin(object_columns),
        ].min()
    ) / (
        df.loc[
            :,
            ~df.columns.isin(object_columns),
        ].max()
        - df.loc[
            :,
            ~df.columns.isin(object_columns),
        ].min()
    )
    df.fillna(0, inplace=True)
    df["score"] = (
        df["Arrivals_accommodation.csv"]
        + df["Net_occupancy_rate.csv"]
        + df["expenditure_accomodation.csv"]
        - df["hicp_per_country.csv"]
        - df["num_of_accoms.csv"]
    )
    df.sort_values(by="score", inplace=True, ignore_index=True, ascending=False)
    nuts_dict = make_nuts2_dict()
    df["location_str"] = df["geo"].apply(lambda x: nuts_dict.get(x))
    result_dict = [{k: v} for k, v in zip(df["location_str"], df["score"])]
    # df.to_csv("location_data.csv")
    return result_dict


if __name__ == "__main__":
    main()
