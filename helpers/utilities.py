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


def select_first_module_from_search_results(url, module_title_prefix):
    search_request = requests.get(url + "pantheon/internal/modules.json?search=" + module_title_prefix)
    search_results = search_request.json()
    if int(search_results["size"]) > 1:
        lcc.log_info("Found more than one result for search: %s, will perform tests for first result..."
                     % module_title_prefix)
        path_for_first_module = search_results["results"][0]["pant:transientPath"]
        lcc.log_info("Further test operations on: %s " % path_for_first_module)
        return path_for_first_module
    else:
        lcc.log_info("no results found for further test operations, either Search API is broken or there is no test data")
        raise Exception
