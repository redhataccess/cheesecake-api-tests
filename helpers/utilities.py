import random
import string
import time, sys
from polling2 import poll
import yaml
import requests
import lemoncheesecake.api as lcc
import os
from helpers import constants
# from urllib.parse import urlencode
import json
# sys.path.append("..")

# setup_test_products = lcc.inject_fixture("setup_test_products")


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


def select_nth_item_from_search_results(n, url, title_prefix):
    search_request = requests.get(url + "pantheon/internal/modules.json?search=" + title_prefix + "&key=Updated date")
    search_results = search_request.json()
    print(str(search_request.content))
    if int(search_results["size"]) >= n:
        lcc.log_info("Found more than one result for search: %s, will perform tests for %s th result..."
                     %(title_prefix,n))
        path_for_nth_module = search_results["results"][n]["pant:transientPath"]
        path_for_nth_module = "content/" + path_for_nth_module
        lcc.log_info("Further test operations on: %s " % path_for_nth_module)
        return path_for_nth_module
    else:
        lcc.log_info("no results found for further test operations, either Search API is broken or there is no test data")
        raise Exception

def fetch_uuid_of_assembly(url, assembly_path, variant):
    assembly_path = url + "content/" + assembly_path + ".7.json"
    assembly_path_endpoint = requests.get(assembly_path)
    print("\n Assembly path: " + assembly_path)
    lcc.log_info("Assembly path being checked: %s" % assembly_path)
    assembly_uuid = assembly_path_endpoint.json()["en_US"]["variants"][variant]["jcr:uuid"]
    print("Assembly uuid: " + str(assembly_uuid))
    return assembly_uuid

def fetch_uuid(url, path, variant):
    path = url + path + ".7.json"
    path_endpoint = requests.get(path)
    print("\n Content path: " + path)
    lcc.log_info("Content path being checked: %s" % path)
    uuid = path_endpoint.json()["en_US"]["variants"][variant]["jcr:uuid"]
    print("uuid: " + str(uuid))
    return uuid

def fetch_json_response_from_adoc_path(url, path):
    request_path = url + path + "7.json"

def add_metadata(url, path, variant, api_auth, setup_test_products, content_type):
    if content_type == "module":
        documentUsecase = constants.documentUsecase
        urlFragment = constants.urlFragment
        searchKeywords = constants.searchKeywords
    elif content_type == "assembly":
        documentUsecase = constants.assembly_documentusecase
        urlFragment = constants.assembly_urlfragment
        searchKeywords = constants.assembly_searchkeywords
    edit_metadata_url = url + path + "/en_US/variants/" + variant + "/draft/metadata"
    print("Data Edit metadata request::", edit_metadata_url)
    lcc.log_info("Data Edit metadata request: %s " % edit_metadata_url)
    # Fetch the product id from fixtures, ta test product and version was created as setup step.
    product_id, product_name_uri = setup_test_products
    print("Data product id::", product_id)
    payload = {"productVersion": product_id,
               "documentUsecase": documentUsecase,
               "urlFragment": urlFragment,
               "searchKeywords": searchKeywords}
    # payload = urlencode(payload)
    print("Payload::", payload)
    # headers = {'content-type': "application/x-www-form-urlencoded"}
    response = api_auth.post(edit_metadata_url, data=payload)
    time.sleep(10)
    print("Response::",response)
    return response, product_name_uri

def publish_content(url, path, variant, api_auth):
    time.sleep(10)
    publish_url = url + path
    print("Request: ",publish_url)
    payload = {
        ":operation": "pant:publish",
        "locale": "en_US",
        "variant": variant
    }
    # headers = {'content-type': "application/x-www-form-urlencoded"}
    # payload = json.dumps(payload)
    # payload = urlencode(payload)
    print("Payload: ",payload)
    response = api_auth.post(publish_url, data=payload)
    time.sleep(10)
    print("Response:", response)
    return response





