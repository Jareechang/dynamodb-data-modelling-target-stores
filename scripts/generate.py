import csv
import pprint
import json
import os

query_attributes = [
    'ID',
    'X.locale',
    'IsDaylightSavingsTimeRecognized',
    'Address.FormattedAddress',
    'PhoneNumber',
    'Address.Subdivision',
    'Address.PostalCode',
    'Address.City',
    'Address.AddressLine1',
    'AllCapability',
    'CVS',
    'Starbucks',
    'CityZip'
]

items_to_view = 10

# View all attributes or just query attributes (by default)
view_all = True

"""
    Utility class to map the array index to the field in the csv data

    Example:

    'PhoneNumber' field is index 29
    'ID' field is index 13

"""
class AttributeIndexMap:

    def __init__(self, labels, query_attributes):
        self.labels = labels;
        self.index_map = {}
        self.all_index_map = {}
        self.query_attributes = query_attributes
        self.create_index()

    """

    create the index mapping

    """
    def create_index(self):
        labels = self.labels
        index_map = self.index_map
        all_index_map = self.all_index_map
        for index, label in enumerate(labels):
            all_index_map[index] = label
            if label in self.query_attributes:
                if label not in index_map:
                    index_map[index] = label
    """

    get the attribute name by the index 

    """
    def get_query_attribute(self, index):
        index_map = self.index_map
        if index in index_map:
            return index_map[index]
        return None

    def get_attribute(self, index):
        all_index_map = self.all_index_map
        if index in all_index_map:
            return all_index_map[index]
        return None

    """

    get all the mapping for the attributes to indices

    @return dictionary -> the dictionary mapping of the all the attributes to indices 

    """
    def get_all(self):
        clone = {}
        for k, v in enumerate(self.index_map):
            clone[k] = v
        return clone


class StoreData():
    def __init__(self, data):
        self.data = data;
        self.gsi_separator = '#'

    """
    return the raw data
    """
    def raw(self):
        clone = {}
        for k, v in self.data.items():
            clone[k] = v
        return clone

    def transformed(self):
        result = self.raw()
        result["AllCapability"] = self.transform_capability(result["AllCapability"])
        # print result["AllCapability"]
        # Convert to int
        result["ID"] = int(result["ID"])
        try:
            result["Store.StoreDistrictID"] = int(result["Store.StoreDistrictID"])
            result["Store.StoreGroupID"] = int(result["Store.StoreGroupID"])
            result["Store.StoreRegionID"] = int(result["Store.StoreRegionID"])
        except KeyError:
            # Fail silently, when we have view_all = False, these fields don't exist
            pass

        starbucks_attr = self.get_ddb_attr(result, "Starbucks")
        if starbucks_attr:
            result["Starbucks"] = starbucks_attr

        cvs_attr = self.get_ddb_attr(result, "CVSpharmacy")
        if cvs_attr:
            result["CVS"] = cvs_attr 
        # Create CityZip GSI
        city_zip_gsi = self.get_ddb_attr(result, "CityZip")
        if city_zip_gsi:
            result["CityZip"] = city_zip_gsi

        return result

    def get_ddb_attr(self, data, gsi_type):
        if gsi_type == "CityZip":
            zip_code = data["Address.PostalCode"]
            city = data["Address.City"]
            if zip_code and city:
                return "{0}#{1}".format(city, zip_code)
            return None

        if (gsi_type == "Starbucks"
                or gsi_type == "CVSpharmacy"):
                all_capability = data["AllCapability"]
                if all_capability and gsi_type in all_capability:
                    return 'True'


    """
    Transform to dynamoDB compatiable query data

    """
    def to_ddb(self):
        result = {}
        transformed_data = self.transformed()
        for k, v in transformed_data.items():
            if type(v) is str:
                result[k] = {
                    'S': v
                }
            if type(v) is int:
                result[k] = {
                    'N': v
                }
        return result

    def transform_capability(self, value):
        if value:
            return (
               value 
                .replace("[", "")
                .replace("]", "")
                .replace(" ", "")
                # re-map some 'e' characters
                .replace("\xe9", "e")
                .replace("\'", "")
                .split(",")
            )
        return value 



def transform_data(labels, data_set):
    results = []
    # Create index mapping
    attribute_index_map = AttributeIndexMap(
        labels,
        query_attributes
    )

    # Fetch transformed data 
    for item in data_set:
        item_condensed = {}
        for n, value in enumerate(item):
            if view_all:
                label_name = attribute_index_map.get_attribute(n)
            else:
                label_name = attribute_index_map.get_query_attribute(n)

            if label_name is not None:
                item_condensed[label_name] = value

        store_data = StoreData(item_condensed)
        results.append(store_data.transformed())

    return results

"""
output the dynamodb inserts
"""
def ddb_inserts_to_csv(output):
    out_file = open("./ddb-inserts.json", "w")
    out_file.write(json.dumps(output))
    out_file.close()


def main():
    # Track number of reads based on the defined var above
    i = 0
    labels = None
    working_data_set = [] 

    # Get the data from csv
    with open("./target.csv") as csv_file:
        readCSV = csv.reader(csv_file, delimiter=',')

        for row in readCSV:
            if i == 0:
                labels = row

            if i < items_to_view and i != 0:
                working_data_set.append(row)
            i += 1

    output = transform_data(labels, working_data_set)
    # print output
    # pprint.pprint(output)
    ddb_inserts_to_csv(output)


if __name__ == "__main__":
    main()

