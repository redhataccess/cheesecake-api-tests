import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll
from helpers import utilities

sys.path.append("..")

module_title_prefix = base.config_reader('test_repo', 'module_prefix')


@lcc.suite(description="Suite: Verify that authenticated user can edit metadata and publish module", rank=1)
class test_module_edit_publish:
  api_auth = lcc.inject_fixture("api_auth")
  path_for_module = ""
  request_url = ""

  @lcc.test("Verify that authenticated user can edit metadata successfully")
  def edit_metadata(self, api_auth, setup_test_products):
    variant = utilities.read_variant_name_from_pantheon2config()
    lcc.log_info(str(variant))
    variant = str(variant)
    self.path_for_module = utilities.select_first_item_from_search_results(fixture.url, module_title_prefix)
    edit_metadata_url = fixture.url + "content/" + self.path_for_module + "/en_US/variants/" +\
                        variant + "/draft/metadata"
    lcc.log_info("Edit metadata request for module: %s " % edit_metadata_url)

    # Fetch the product id from fixtures, ta test product and version was created as setup step.
    product_id = setup_test_products
    payload = {"productVersion": product_id,
               "documentUsecase": constants.documentUsecase,
               "urlFragment": constants.urlFragment,
               "searchKeywords": constants.searchKeywords}
    edit_metadata_request = self.api_auth.post(edit_metadata_url, data = payload)
    self.request_url = fixture.url + "content/" + self.path_for_module + ".7.json"
    #check that metadata has been added successfully.
    response = api_auth.get(self.request_url)
    metadata_response = response.json()["en_US"]["variants"][variant]["draft"]["metadata"]
    check_that("The edit metadata request was successful", edit_metadata_request.status_code, equal_to(200))
    check_that("The product version has been updated successfully", metadata_response["productVersion"],
               equal_to(product_id))
    check_that("The document use case has been updated successfully", metadata_response["documentUsecase"],
               equal_to(constants.documentUsecase))

  @lcc.test("Verify that authenticated user can publish module successfully")
  def publish_module(self, api_auth):
    variant = utilities.read_variant_name_from_pantheon2config()
    lcc.log_info(str(variant))
    variant = str(variant)
    # Get path of the module for which metadata was added
    publish_url = fixture.url + self.path_for_module
    payload = {
        ":operation": "pant:publish",
        "locale": "en_US",
        "variant": variant
    }
    publish_module_request = self.api_auth.post(publish_url, data=payload)
    check_that("The publish request was successful", publish_module_request.status_code, equal_to(200))
    response = api_auth.get(self.request_url)
    # Check that the node has been marked as released
    check_that("The published module now has a 'released' node", response.json()["en_US"]["variants"][variant],
               contains_string("released"))



