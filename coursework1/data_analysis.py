import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import copy


def rename_column(df: pd.DataFrame, name_map: dict):
    """Do feature cleaning, such as renaming the column names.
    """
    df.columns = df.columns.str.strip()
    df.rename(columns=name_map, inplace=True)
    return df


def analysis_district_population0(df: pd.DataFrame):
    """Analysis population in each district.
       United Kingdom = Great Britain + Northern Ireland
       Great Britian = Englang and Wales + Scotland
       Englang and Wales = England + Wales
    """
    district_name = ["England", "Wales", "Scotland", "Northern Ireland"]
    population_list = [df.loc[0, name] for name in district_name]
    district_name[3] = "Northern\nIreland"
    explode = (0.05, 0, 0, 0)
    
    plt.figure(figsize=(12, 12))
    plt.pie(population_list, explode=explode, labels=district_name, autopct='%1.1f%%', 
            textprops={"fontsize": 14})
    plt.title("Population distribution of United Kingdom", fontsize=18, fontweight='bold')
    plt.axis("equal")
    plt.savefig("uk_pop_pie.png")


def analysis_district_population1(df: pd.DataFrame):
    """Analysis sex distribution population in each district.
    """
    district_name = ["England", "Wales", "Scotland", "Northern Ireland"]
    scale_factor = 1e6
    female_list = [round(df.loc[1, name] / scale_factor, 2) for name in district_name]
    male_list = [round(df.loc[2, name] / scale_factor, 2) for name in district_name]
    district_name[3] = "Northern\nIreland"
    
    bottom = [0 for _ in range(len(district_name))]
    
    fig = plt.figure(figsize=(16, 14))
    ax = fig.add_subplot(1, 1, 1)
    p = ax.bar(district_name, female_list, width=0.68, label="Female", bottom=bottom)
    ax.bar_label(p, label_type="center", fontsize=14)
    p = ax.bar(district_name, male_list, width=0.68, label="male", bottom=female_list)
    ax.bar_label(p, label_type="center", fontsize=14)
    ax.tick_params(axis='x', labelsize=16)
    ax.set_xlabel("Districts in UK", fontsize=16)
    ax.set_ylabel("Numbers (million)", fontsize=16)
    ax.legend(fontsize=16)

    plt.title("Population distribution of United Kingdom", fontsize=25, fontweight='bold')
    plt.savefig("uk_pop_sex.png")


def analysis_age_distribution(df: pd.DataFrame):
    """Analysis age distribution in each district

    Args:
        df (pd.DataFrame): input of the dataframe
    """
    district_name = ["England", "Wales", "Scotland", "Northern Ireland"]
    scale_factor = 1e6
    
    for name in district_name:
        df[name] = df[name].apply(lambda x: round(x / scale_factor, 2))
    
    age_name = df["Age Groups"].apply(lambda s: s.split(" ")[0] + "-" + s.split(" ")[2]).tolist()
    for s in age_name:
        if len(s) < 7:
            pad_size = (7 - len(s)) // 2
            s = " " * pad_size + s + " " * pad_size
   
    district_list = []
    
    for name in district_name:
        district_list.append(df[name].to_list())
    
    plt.figure(figsize=(12, 8))
    for i in range(len(district_name)):
        plt.plot(age_name, district_list[i], label=district_name[i])
    
    plt.legend()
    plt.xlabel("Age Groups", fontsize=16)
    plt.ylabel("Number (million)", fontsize=16)
    plt.title("Population distribution of different ages in each district of UK", fontsize=21, fontweight='bold')
    plt.savefig("uk_age_distribution.png")


def ERD_database(df: pd.DataFrame):
    print(df.head())
    district_names = df.columns.tolist()[1:]
    district_ID = [i for i in range(len(district_names))]
    district_map = {name: id for id, name in enumerate(district_names)}
    distict_data = {
        "DistrictID": district_ID,
        "DistrictName": district_names
    }
    district_df = pd.DataFrame(distict_data)
    
    age_groups = df["Age Groups"].tolist()
    age_groups_ID = [i for i in range(len(age_groups))]
    age_groups_data = {
        "AgeGroupID": age_groups_ID,
        "AgeRange": age_groups
    }
    age_groups_df = pd.DataFrame(age_groups_data)

    v_list = []
    district_id_list = []
    age_group_id_list = []
    for index, row in df.iterrows():
        for col_name in df.columns[1:]:
            v = row[col_name]
            v_list.append(v)
            district_id_list.append(district_map[col_name])
            age_group_id_list.append(index)
    pData_id = [i for i in range(len(v_list))]
    population_data = {
        "populationDataId": pData_id,
        "population": v_list,
        "DistrictId": district_id_list,
        "AgeGroupID": age_group_id_list
    }
    population_df = pd.DataFrame(population_data)
    
    db_conn = sqlite3.connect("population.db")
    
    c = db_conn.cursor()
    c.execute("DROP TABLE IF EXISTS district")
    c.execute("DROP TABLE IF EXISTS ageGroup")
    c.execute("DROP TABLE IF EXISTS populationData")
    c.execute(
        """
        CREATE TABLE district (
            DistrictID INTEGER ,
            DistrictName TEXT NOT NULL,
            PRIMARY KEY(DistrictID)
            );
        """
    )
    c.execute(
        """
        CREATE TABLE ageGroup (
            AgeGroupID INTEGER ,
            AgeRange TEXT NOT NULL,
            PRIMARY KEY(AgeGroupID)
            );
        """
    )
    c.execute(
        """
        CREATE TABLE populationData (
            populationDataId INTEGER ,
            DistrictId INTEGER,
            AgeGroupID INTEGER,
            population INTEGER,
            PRIMARY KEY(populationDataId)
            FOREIGN KEY(DistrictId) REFERENCES district(DistrictId),
            FOREIGN KEY(AgeGroupID) REFERENCES ageGroup(AgeGroupID)
            );
        """
    )
    
    district_df.to_sql('district', db_conn, if_exists='append', index=False)
    age_groups_df.to_sql('ageGroup', db_conn, if_exists='append', index=False)
    population_df.to_sql('populationData', db_conn, if_exists='append', index=False)
    
    print(pd.read_sql("SELECT * FROM populationData LIMIT 10", db_conn))
    
    db_conn.close()
    


if __name__ == "__main__":
    # column renmae map
    column_map = {"England \nand Wales": "England and Wales"}
    
    population_df = pd.read_excel("./population.xlsx", sheet_name="Sheet1")
    rename_column(population_df, column_map)
    analysis_district_population0(population_df)
    analysis_district_population1(population_df)
    
    distribution_df = pd.read_excel("./population.xlsx", sheet_name="Sheet2")
    distribution_database_df = copy.deepcopy(distribution_df)
    rename_column(distribution_df, column_map)
    analysis_age_distribution(distribution_df)
    
    rename_column(distribution_database_df, column_map)
    ERD_database(distribution_database_df)
    