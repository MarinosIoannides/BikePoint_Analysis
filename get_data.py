"""
get_data.py
-----------
This script uses APIs to gather the data relevant for the analysis and the model run.
These are all stored in the Data/ folder.

This is performed in advance of the model's run to make sure the data is quickly available.
"""
import requests
import urllib3
import polars as pl

urllib3.disable_warnings()
# File path where data will be stored
file_path = "data/"

def get_bikepoints(bikepoint_api):
    """
    A function which visits the bikepoint_api and both returns the data as a dataframe and outputs it to a csv.

    Parameters
    ----------
    bikepoint_api: str
        The API where the bikepoint data is available. Usually https://api.tfl.gov.uk/BikePoint/
    
    Returns
    --------
    cycle_dataframe: dataframe
        A dataframe of all the data at the API except "additionalProperties".
    
    Raises
    ------
    Type Error
        If input is not str.
    Index Error
        If there is something wrong with the API and it does not return code 200.
    
    # TODO: Consider changing column names to underscore_style for neatness of output.
    """
    if type(bikepoint_api) != str:
        raise TypeError("The API must be a string.")

    r = requests.get(bikepoint_api)
    if r.status_code == 200:
        bikepoints = pl.read_json(r.content)
    else:
        raise IndexError(f"API Error: {r.status_code}")
    bikepoints = bikepoints.drop("additionalProperties")
    bikepoints.write_csv(file = file_path + "bikepoints.csv")
    return bikepoints

bikepoint_dataframe = get_bikepoints("https://api.tfl.gov.uk/BikePoint/")

def lat_long_translate(postcodes_api, bikepoints):
    """
    A function which takes a dataframe of latitudes and logitudes and counts how many are in each local authority.

    Parameters
    ----------
    postcodes: str
        The API where the postcode translation is available. Usually https://api.postcodes.io/postcodes
    bikepoints: dataframe
        The dataframe containing all the latitudes and logitudes of the dataframe
    
    Returns
    --------
    la_dataframe: dataframe
        A dataframe with two columns: la_name and counts
    
    Raises
    ------
    Type Error
        If postcodes_api is not str.
    
    # TODO: There must be a neater way of doing this. Come back if time.
    # TODO: Make it work with polars and pandas dataframes
    """
    if type(postcodes_api) != str:
        raise TypeError("The API must be a string.")
    list_of_locations = list(zip(list(bikepoints["lat"]), list(bikepoints["lon"])))
    las = {}
    for loop in range(0, int(len(list_of_locations)/100)):
        # The API wants the information in a list of dictionaries, each of which has an individual logitude / latitude
        request_list = []
        # The API only handles inputs in batches of 100
        for location in list_of_locations[loop*100: loop*100 + 100]:
            loc_dict = {
                "longitude":  location[1],
                "latitude": location[0],
                "limit":1,
                "radius":300,
            }
            request_list.append(loc_dict)
        request_dict = {
            "geolocations" : request_list
            }
        r = requests.post(postcodes_api, json = request_dict, verify = False)
        for i in range(0, 100):
            raw_data = r.json()["result"][i]["result"][0].pop("codes")
            this_location = pl.DataFrame(raw_data)
            if "parliamentary_constituency" in this_location.columns:
                las.setdefault(this_location["lsoa"][0], 0)
                las[this_location["lsoa"][0]] += 1
    la_table = pl.DataFrame(las)
    la_table = la_table.transpose(include_header=True, header_name="lsoa", column_names = ["count"])
    la_table.write_csv(file = file_path + "la_counts.csv", separator= ",")
    return la_table

la_counts_dataframe = lat_long_translate("https://api.postcodes.io/postcodes", bikepoint_dataframe)