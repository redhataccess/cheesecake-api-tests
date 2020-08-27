import random
import string
import time, sys
from polling2 import poll
import yaml
import requests
import lemoncheesecake.api as lcc
import os
# sys.path.append("..")


def generate_random_string(string_length):
    # Generate a random string of fixed length
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(string_length))
    return random_string


def read_variant_name_from_pantheon2config():
    print(os.getcwd())
    pantheon_config = yaml.safe_load(open('./pantheon2.yml', 'r'))
    for variant in pantheon_config["variants"]:
        if variant["canonical"] == True:
            variant = variant["name"]
            lcc.log_info("Variant name used: %s" % variant)
            return str(variant)


def select_first_item_from_search_results(url, title_prefix):
    search_request = requests.get(url + "pantheon/internal/modules.json?search=" + title_prefix + "&key=Updated date")
    search_results = search_request.json()
    print(str(search_request.content))
    if int(search_results["size"]) > 0:
        lcc.log_info("Found more than one result for search: %s, will perform tests for first result..."
                     % title_prefix)
        path_for_first_module = search_results["results"][0]["pant:transientPath"]
        lcc.log_info("Further test operations on: %s " % path_for_first_module)
        return path_for_first_module
    else:
        lcc.log_info("no results found for further test operations, either Search API is broken or there is no test data")
        raise Exception

def fetch_uuid_of_assembly(url, assembly_path, variant):
    assembly_path = url + "content/" + assembly_path + ".7.json"
    assembly_path_endpoint = requests.get(assembly_path)
    print(assembly_path)
    assembly_uuid = assembly_path_endpoint.json()["en_US"]["variants"][variant]["jcr:uuid"]
    print("Assembly uuid: " + str(assembly_uuid))
    return assembly_uuid


