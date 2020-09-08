import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll
from helpers import utilities
import urllib.parse

sys.path.append("..")

module_title_prefix = base.config_reader('test_repo', 'module_prefix')
global test_product_id

@lcc.suite(description="Suite: Verify that authenticated user can edit metadata and publish module", rank=1)
class test_module_edit_publish:
  api_auth = lcc.inject_fixture("api_auth")
  path_for_module = ""
  request_url = ""

  @lcc.test("Verify that authenticated user can edit metadata successfully")
  def edit_metadata(self, api_auth, setup_test_products):
    self.variant = utilities.read_variant_name_from_pantheon2config()
    lcc.log_info(str(self.variant))
    self.variant = str(self.variant)
    self.path_for_module = utilities.select_first_item_from_search_results(fixture.url, module_title_prefix)
    edit_metadata_url = fixture.url + "content/" + self.path_for_module + "/en_US/variants/" +\
                        self.variant + "/draft/metadata"
    lcc.log_info("Edit metadata request for module: %s " % edit_metadata_url)

    # Fetch the product id from fixtures, ta test product and version was created as setup step.
    product_id, product_name_uri = setup_test_products
    payload = {"productVersion": product_id,
               "documentUsecase": constants.documentUsecase,
               "urlFragment": constants.urlFragment,
               "searchKeywords": constants.searchKeywords}
    edit_metadata_request = self.api_auth.post(edit_metadata_url, data = payload)
    self.request_url = fixture.url + "content/" + self.path_for_module + ".7.json"
    #check that metadata has been added successfully.
    response = api_auth.get(self.request_url)
    metadata_response = response.json()["en_US"]["variants"][self.variant]["draft"]["metadata"]
    check_that("The edit metadata request was successful", edit_metadata_request.status_code, equal_to(200))
    check_that("The product version has been updated successfully", metadata_response["productVersion"],
               equal_to(product_id))
    check_that("The document use case has been updated successfully", metadata_response["documentUsecase"],
               equal_to(constants.documentUsecase))

  @lcc.test("Verify that authenticated user can publish module successfully")
  def publish_module(self, api_auth):
    # Get path of the module for which metadata was added
    publish_url = fixture.url + self.path_for_module
    payload = {
        ":operation": "pant:publish",
        "locale": "en_US",
        "variant": self.variant
    }
    publish_module_request = self.api_auth.post(publish_url, data=payload)
    check_that("The publish request was successful", publish_module_request.status_code, equal_to(200))
    response = api_auth.get(self.request_url)
    # Check that the node has been marked as released
    check_that("The published module now has a 'released' node", response.json()["en_US"]["variants"][self.variant],
               contains_string("released"))

    module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant)
    published_module_url = fixture.url + "api/module/variant.json/" + module_uuid
    print("published module url: \n" + published_module_url)
    lcc.log_info("Published Module api endpoint: %s" % published_module_url)
    data_from_published_module = api_auth.get(published_module_url)
    check_that("The /api/module/variant.json/<module_uuid> endpoint for a published module",
               data_from_published_module.status_code, equal_to(200))

    print("Response from published module API endpoint: \n" + str(data_from_published_module.content))
    check_that("The response is ", data_from_published_module.json()["message"], equal_to("Module Found"))
    check_that("The title of the module ", data_from_published_module.json()["module"]["title"],
               contains_string(module_title_prefix))
    check_that("The status of the module ", data_from_published_module.json()["module"]["status"],
               equal_to("published"))
    check_that("The body of the module", data_from_published_module.json()["module"]["body"], is_not_none())





