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


@lcc.suite("Suite: Verify that authenticated user can edit metadata and publish module", rank=1)
class test_module_edit_publish:
  api_auth = lcc.inject_fixture("api_auth")

  @lcc.test("Verify that authenticated user can edit metadata successfully")
  def edit_metadata(self, api_auth, setup_test_products):
    variant = utilities.read_variant_name_from_pantheon2config()
    lcc.log_info(str(variant))
    variant = str(variant)
    path_for_module = utilities.select_first_module_from_search_results(fixture.url, module_title_prefix)
    edit_metadata_url = fixture.url + "content/" + path_for_module + "/en_US/variants/" +\
                        variant + "/draft/metadata"
    lcc.log_info("Edit metadata request for module: %s " % edit_metadata_url)

    # Fetch the product id from fixtures, ta test product and version was created as setup step.
    product_id = setup_test_products
    payload = {"productVersion": product_id,
               "documentUsecase": constants.documentUsecase,
               "urlFragment": constants.urlFragment,
               "searchKeywords": constants.searchKeywords}
    edit_metadata_request = self.api_auth.post(edit_metadata_url, data = payload)
    request_url = fixture.url + "content/" + path_for_module + ".7.json"
    #check that metadata has been added successfully.
    response = api_auth.get(request_url)
    metadata_response = response.json()["en_US"]["variants"][variant]["draft"]["metadata"]
    check_that("The edit metadata request was successful", edit_metadata_request.status_code, equal_to(200))
    check_that("The product version has been updated successfully", metadata_response["productVersion"],
               equal_to(product_id))
    check_that("The document use case has been updated successfully", metadata_response["documentUsecase"],
               equal_to(constants.documentUsecase))


