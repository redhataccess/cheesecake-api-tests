import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll
from helpers import utilities
# from urllib.parse import urlencode
import json
import time

sys.path.append("..")

module_title_prefix = base.config_reader('test_repo', 'module_prefix')
module_uuid = ""

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
    self.path_for_module = utilities.select_nth_item_from_search_results(0, fixture.url, module_title_prefix)
    edit_metadata_url = fixture.url + self.path_for_module + "/en_US/variants/" +\
                        self.variant + "/draft/metadata"
    lcc.log_info("Edit metadata request for module: %s " % edit_metadata_url)

    # Fetch the product id from fixtures, ta test product and version was created as setup step.
    product_id, product_name_uri = setup_test_products
    payload = {"productVersion": product_id,
               "documentUsecase": constants.documentUsecase,
               "urlFragment": constants.urlFragment,
               "searchKeywords": constants.searchKeywords}
    # payload = urlencode(payload)
    print("PAyload::", payload)
    # headers = {'content-type': "application/x-www-form-urlencoded"}
    edit_metadata_request = self.api_auth.post(edit_metadata_url, data = payload)
    time.sleep(10)
    print("Response::", edit_metadata_request)
    self.request_url = fixture.url + self.path_for_module + ".10.json"
    #check that metadata has been added successfully.
    response = api_auth.get(self.request_url)
    print("Response::",response)
    metadata_response = response.json()["en_US"]["variants"][self.variant]["draft"]["metadata"]
    print("Metadata response::", metadata_response)
    check_that("The edit metadata request was successful", edit_metadata_request.status_code,
               any_of(equal_to(200), equal_to(201)))
    check_that("The product version has been updated successfully", metadata_response["productVersion"],
               equal_to(product_id))
    check_that("The document use case has been updated successfully", metadata_response["documentUsecase"],
               equal_to(constants.documentUsecase))

  @lcc.test("Verify that authenticated user can publish module successfully")
  def publish_module(self, api_auth):
    # Get path of the module for which metadata was added
    publish_url = fixture.url + self.path_for_module
    print("\n API end point used for publish request: " + publish_url)
    payload = {
        ":operation": "pant:publish",
        "locale": "en_US",
        "variant": self.variant
    }

    print("Payload: ", payload)
    time.sleep(10)
    publish_module_request = self.api_auth.post(publish_url, data=payload)
    time.sleep(10)
    check_that("The publish request was successful", publish_module_request.status_code, equal_to(200))
    response = api_auth.get(self.request_url)
    # Check that the node has been marked as released
    check_that("The published module now has a 'released' node", response.json()["en_US"]["variants"][self.variant],
               contains_string("released"))

    self.module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant)
    published_module_url = fixture.url + "api/module/variant.json/" + self.module_uuid
    print("published module url: \n" + published_module_url)
    lcc.log_info("Published Module api endpoint: %s" % published_module_url)
    data_from_published_module = api_auth.get(published_module_url)
    check_that("The /api/module/variant.json/<module_uuid> endpoint for a published module",
               data_from_published_module.status_code, equal_to(200))

    # print("Response from published module API endpoint: \n" + str(data_from_published_module.content))
    check_that("The response is ", data_from_published_module.json()["message"], equal_to("Module Found"))
    check_that("The title of the module ", data_from_published_module.json()["module"]["title"],
               contains_string(module_title_prefix))
    check_that("The status of the module ", data_from_published_module.json()["module"]["status"],
               equal_to("published"))
    check_that("The body of the module", data_from_published_module.json()["module"]["body"], is_not_none())

  @lcc.test("Verify that acknowledgement was received from Hydra")
  def ack_status_check(self, api_auth):
    #self.request_module_url = fixture.url + self.path_for_module + ".10.json"
    time.sleep(10)
    response = api_auth.get(self.request_url)
    time.sleep(10)
    response = api_auth.get(self.request_url)
    lcc.log_info("Checking for ack_status at url: %s" % str(self.request_url))
    check_that("The published module now has a released node with ack_status node ",
               response.json()["en_US"]["variants"][self.variant]["released"], has_entry("ack_status"))
    lcc.log_info("Ack status node response: %s" % str(response.json()["en_US"]["variants"][self.variant]["released"]["ack_status"]))
    check_that("The published module has a successful message from Hydra",
               response.json()["en_US"]["variants"][self.variant]["released"]["ack_status"]["pant:message"],
               equal_to("Solr call for index was successful"))

    check_that("The published module has a successful ACK from Hydra",
               response.json()["en_US"]["variants"][self.variant]["released"]["ack_status"]["pant:status"],
               equal_to("SUCCESSFUL"))


  @lcc.test("Verify that the module was indexed in Solr in docv2 collection")
  def verify_solr_indexing(self):
    # Reusing the module id fetched in the above test
    time.sleep(15)
    solr_request_url = fixture.solr_url + "solr/docv2/select?indent=on&q=id:" + self.module_uuid + "&wt=json"
    lcc.log_info("Checking docv2 collection in Solr: %s" % solr_request_url)
    solr_request = requests.get(solr_request_url)
    solr_request_json = solr_request.json()
    lcc.log_info("Response from Solr: %s " % str(solr_request_json))
    check_that("The module is indexed in docv2 collection in Solr", solr_request_json["response"]["numFound"], equal_to(1))
    check_that("The content type", solr_request_json["response"]["docs"][0]["content_type"][0], equal_to("module"))

  @lcc.test("Verify if the module is available for search in access collection")
  def verify_solr_access_collection_module(self):
    time.sleep(40)
    solr_request_url = fixture.solr_url + "solr/access/select?indent=on&q=id:" + self.module_uuid + "&wt=json"
    lcc.log_info("Checking access collection in Solr: %s" % solr_request_url)
    solr_request = requests.get(solr_request_url)
    time.sleep(10)
    solr_request = requests.get(solr_request_url)
    solr_request_json = solr_request.json()
    lcc.log_info("Response from Solr: %s " % str(solr_request_json))
    check_that("The module is indexed in access collection in Solr", solr_request_json["response"]["numFound"],
               equal_to(1))
    # add more checks here.
    check_that("The content type source ", solr_request_json["response"]["docs"][0]["source"], equal_to("module"))

  @lcc.test("Verify that the module is successfully unpublished, Hydra sends an ACK")
  def unpublish_module(self, api_auth):
    unpublish_url = fixture.url + self.path_for_module
    lcc.log_info("Unpublishing the module: %s" % unpublish_url)
    payload = {
      ":operation": "pant:unpublish",
      "locale": "en_US",
      "variant": self.variant
    }
    unpublish_module_request = self.api_auth.post(unpublish_url, data=payload)
    time.sleep(15)
    check_that("Unpublish request status code", unpublish_module_request.status_code, equal_to(200))
    response = api_auth.get(self.request_url)
    time.sleep(10)
    response = api_auth.get(self.request_url)
    lcc.log_info("Checking for ack_status at url after unpublish: %s" % str(self.request_url))
    check_that("The unpublished module now has a draft node with ack_status node ",
               response.json()["en_US"]["variants"][self.variant]["draft"], has_entry("ack_status"))
    lcc.log_info("Ack status node response: %s" % str(response.json()["en_US"]["variants"][self.variant]["draft"]["ack_status"]))
    # this is a place holder check
    check_that("The unpublished module has a successful message from Hydra",
               response.json()["en_US"]["variants"][self.variant]["draft"]["ack_status"]["pant:message"],
               equal_to("Solr call for delete was successful"))

    check_that("The unpublished module has a successful ACK from Hydra",
               response.json()["en_US"]["variants"][self.variant]["draft"]["ack_status"]["pant:status"],
               equal_to("SUCCESSFUL"))

  @lcc.test("Verify if the module is successfully removed from docv2 and Solr collection")
  def removed_from_solr(self):
    time.sleep(20)
    solr_request_url = fixture.solr_url + "solr/docv2/select?indent=on&q=id:" + self.module_uuid + "&wt=json"
    lcc.log_info("Checking docv2 collection in Solr: %s" % solr_request_url)
    solr_request = requests.get(solr_request_url)
    solr_request_json = solr_request.json()
    lcc.log_info("Response from Solr: %s " % str(solr_request_json))
    check_that("The module is removed from docv2 collection in Solr", solr_request_json["response"]["numFound"],
               equal_to(0))

    lcc.log_info("Checking if the assembly is removed from search results, access collection")
    time.sleep(20)
    solr_request_url = fixture.solr_url + "solr/access/select?indent=on&q=id:" + self.module_uuid + "&wt=json"
    lcc.log_info("Checking access collection in Solr: %s" % solr_request_url)
    solr_request = requests.get(solr_request_url)
    solr_request_json = solr_request.json()
    lcc.log_info("Response from Solr: %s " % str(solr_request_json))
    check_that("The module is removed from access collection in Solr", solr_request_json["response"]["numFound"],
               equal_to(0))
