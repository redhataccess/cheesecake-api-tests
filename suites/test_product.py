import sys
import requests
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
import shutil, time, datetime
from fixtures.fixture import url, product_name_uri, product_name, username, auth
from helpers import constants
import subprocess


@lcc.suite(description="Suite: verify product info ", rank=7)
class test_product:
    api_auth = lcc.inject_fixture("api_auth")
    path_to_product = url + "content/products/" + product_name_uri

    @lcc.test("Verify product info : uuid, name, sling:resourceType, jcr:primaryType")
    def verify_product_info(self):
        lcc.log_info("Test Product node being created at: %s" % self.path_to_product)
        create_product_payload = {"name": product_name,
                                  "description": "Test product Setup description",
                                  "sling:resourceType": "pantheon/product",
                                  "jcr:primaryType": "pant:product",
                                  "locale": "en-US",
                                  "urlFragment": product_name_uri}

        # Hit the api for create product
        response = requests.post(self.path_to_product, data=create_product_payload, auth=(username, auth))
        check_that("The Product is created successfully",
                   response.status_code, any_of(equal_to(201), equal_to(200)))

        # Hit the api to get id of created product
        get_product_id_endpoint = self.path_to_product + ".json"
        product_id_request = requests.get(get_product_id_endpoint)
        check_that("%s API status code" % get_product_id_endpoint, product_id_request.status_code, equal_to(200))
        product_id = product_id_request.json()
        check_that("Product uuid", product_id["jcr:uuid"], is_not_none())
        check_that("sling:resourceType", product_id["sling:resourceType"], equal_to("pantheon/product"))
        check_that("jcr:primaryType", product_id["jcr:primaryType"], equal_to("pant:product"))
        check_that("product name", product_id["name"], equal_to(product_name))

    @lcc.test("Verify product version info : uuid, name, sling:resourceType, jcr:primaryType")
    def verify_product_version_info(self):
        path_to_version = self.path_to_product + "/versions/{}".format(constants.product_version)
        lcc.log_info("Product version being created for the above product: %s" % path_to_version)

        create_version_payload = {"name": constants.product_version,
                                  "sling:resourceType": "pantheon/productVersion",
                                  "jcr:primaryType": "pant:productVersion",
                                  "urlFragment": constants.product_version_uri}

        # Hit the api for create version for the above product
        response = requests.post(path_to_version, data=create_version_payload, auth=(username, auth))
        check_that("The Product version is created successfully",
                   response.status_code, any_of(equal_to(201), equal_to(200)))

        # Hit the api to get id of product version
        path_to_product_id = self.path_to_product + "/versions/" + constants.product_version + ".json"
        product_version_id_req = requests.get(path_to_product_id)
        check_that("%s API status code" % path_to_product_id, product_version_id_req.status_code, equal_to(200))
        product_version_id = product_version_id_req.json()
        check_that("Product version uuid", product_version_id["jcr:uuid"], is_not_none())
        check_that("sling:resourceType", product_version_id["sling:resourceType"], equal_to("pantheon/productVersion"))
        check_that("jcr:primaryType", product_version_id["jcr:primaryType"], equal_to("pant:productVersion"))
        check_that("product version", product_version_id["name"], equal_to(constants.product_version))

    def teardown_suite(self):
        session = requests.Session()
        session.auth = (username, auth)
        # lcc.log_info("Deleting test products created as a part of the tests.. ")
        path_to_new_product_node = url + "bin/cpm/nodes/node.json/content/products/" + product_name_uri
        lcc.log_info("Test Product node being deleted at: %s" % path_to_new_product_node)
        try:
            response1 = session.delete(path_to_new_product_node)
            check_that("Test product version created was deleted successfully",
                       response1.status_code, equal_to(200))
        except Exception as e:
            lcc.log_info(e)
