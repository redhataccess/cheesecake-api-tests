import sys, os
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from helpers import constants
import requests
import time
from fixtures import fixture
from polling2 import poll
from helpers import utilities
import json
# from urllib.parse import urlencode

sys.path.append("..")

assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')


@lcc.suite(description="Suite: Tests for Assemblies", rank=3)
class test_assembly_edit_publish:
    api_auth = lcc.inject_fixture("api_auth")
    global product_id

    @lcc.test("Verify that authenticated user can edit metadata for an assembly successfully")
    def verify_edit_metadata(self, setup_test_products, api_auth):
        self.variant = utilities.read_variant_name_from_pantheon2config()
        lcc.log_info(str(self.variant))
        self.variant = str(self.variant)
        self.path_for_assembly = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_title_prefix,api_auth)

        edit_metadata_url = fixture.url + self.path_for_assembly + "/en_US/variants/" + \
                            self.variant + "/draft/metadata"
        lcc.log_info("Edit metadata request for assembly at : %s " % edit_metadata_url)

        # Fetch the product id from fixtures/fixtures.py, the test product and version was created as a setup step.
        product_id, product_name_uri = setup_test_products

        payload = {"productVersion": product_id,
                   "documentUsecase": constants.assembly_documentusecase,
                   "urlFragment": constants.assembly_urlfragment,
                   "searchKeywords": constants.assembly_searchkeywords}
        # payload = urlencode(payload)
        print("Payload::", payload)
        # headers = {'content-type': "application/x-www-form-urlencoded"}
        edit_metadata_request = self.api_auth.post(edit_metadata_url, data=payload)
        print(edit_metadata_request)
        time.sleep(10)
        check_that("Edit metadata request to be successful", edit_metadata_request.status_code, equal_to(200))
        request_url = fixture.url + self.path_for_assembly + ".7.json"


        #check that metadata has been added successfully.
        response = self.api_auth.get(request_url)
        metadata_response = response.json()["en_US"]["variants"][self.variant]["draft"]["metadata"]
        check_that("The edit metadata request was successful", edit_metadata_request.status_code,
                   any_of(equal_to(200), equal_to(201)))
        check_that("The product version has been updated successfully", metadata_response["productVersion"],
                   equal_to(product_id))
        check_that("The document use case has been updated successfully", metadata_response["documentUsecase"],
                   equal_to(constants.assembly_documentusecase))
        check_that("The search keywords have been updated successfully", metadata_response["searchKeywords"],
                   equal_to(constants.assembly_searchkeywords))
        check_that("The URL fragment has been updated successfully", metadata_response["urlFragment"],
                   equal_to(constants.assembly_urlfragment))


    @lcc.test("Verify that the user can publish an assembly successfully and check for /api/assembly/variant.json/"
              "<assembly_uuid> endpoint")
    def verify_publish_assembly(self, api_auth):
        # print("variant: " + self.variant)
        payload = {":operation": "pant:publish",
                   "locale": "en_US",
                   "variant": self.variant
                   }
        # headers = {'content-type': "application/x-www-form-urlencoded"}
        # payload = json.dumps(payload)
        # payload = urlencode(payload)
        print("Payload: ",payload)
        publish_url = fixture.url + self.path_for_assembly
        lcc.log_info("API end point used for publish request: %s" % publish_url)
        time.sleep(15)
        publish_request = api_auth.post(publish_url, data=payload, headers={'Accept': 'application/json'})
        lcc.log_info("Publish request response: \n %s" % str(publish_request.content))
        time.sleep(10)
        check_that("The publish request is successful", publish_request.status_code, equal_to(200))

        # Check if the publish request response returns "url" for Customer Portal: CCS-3860
        cp_url_returned = publish_request.json()["location"]
        check_that("Publish assembly response contains The Customer Portal URL", cp_url_returned,
                   contains_string(fixture.cp_url + "documentation"))

        req = api_auth.get(fixture.url + self.path_for_assembly + ".7.json")

        check_that("The status node in variants > variant >: ", req.json()["en_US"]["variants"][self.variant],
                   has_entry("released"), quiet=True)

        self.assembly_uuid = utilities.fetch_uuid(fixture.url, self.path_for_assembly, self.variant, api_auth)

        published_assembly_url = fixture.url + "api/assembly/variant.json/" + self.assembly_uuid
        print("published assembly url: \n" + published_assembly_url)
        lcc.log_info("Published Assembly api endpoint: %s" % published_assembly_url)
        published_assembly_request = api_auth.get(published_assembly_url)
        check_that("The /api/assembly/variant.json/<assembly_uuid> endpoint for a published assembly",
                   published_assembly_request.status_code, equal_to(200))

        # print("Response from published assembly API endpoint: \n" + str(published_assembly_request.content))
        check_that("The response is ", published_assembly_request.json()["message"], equal_to("Assembly Found"))
        check_that("The title of the assembly ", published_assembly_request.json()["assembly"]["title"],
                   contains_string(assembly_title_prefix))
        check_that("The status of the assembly ", published_assembly_request.json()["assembly"]["status"],
                   equal_to("published"))
        check_that("The content type of the assembly", published_assembly_request.json()["assembly"]["content_type"],
                   equal_to("assembly"))
        check_that("The body of the assembly", published_assembly_request.json()["assembly"]["body"], is_not_none())
        #add a check for date_published, search_keywords, etc.

    @lcc.test("Verify that acknowledgement was received from Hydra on publishing assembly")
    def ack_status_check(self, api_auth):
      self.request_url = fixture.url + self.path_for_assembly + ".10.json"
      response  = api_auth.get(self.request_url)
      time.sleep(60)
      #calling the get request twice
      response = api_auth.get(self.request_url)
      lcc.log_info("Checking for ack_status at url: %s" % str(self.request_url))
      check_that("The published assembly now has a released node with ack_status node ",
                 response.json()["en_US"]["variants"][self.variant]["released"], has_entry("ack_status"))
      lcc.log_info("Ack status node response: %s" % str(
        response.json()["en_US"]["variants"][self.variant]["released"]["ack_status"]))
      check_that("The published assembly has a successful message from Hydra",
                 response.json()["en_US"]["variants"][self.variant]["released"]["ack_status"]["pant:message"],
                 equal_to("Solr call for index was successful"))

      check_that("The published assembly has a successful ACK from Hydra",
                 response.json()["en_US"]["variants"][self.variant]["released"]["ack_status"]["pant:status"],
                 equal_to("SUCCESSFUL"))

    @lcc.test("Verify that the assembly was indexed in Solr in docv2 collection")
    def verify_solr_docv2_indexing_assembly(self):
      # Reusing the module id fetched in the above test
      time.sleep(15)
      solr_request_url = fixture.solr_url + "solr/docv2/select?indent=on&q=id:" + self.assembly_uuid + "&wt=json"
      lcc.log_info("Checking docv2 collection in Solr: %s" % solr_request_url)
      solr_request = requests.get(solr_request_url)
      time.sleep(10)
      solr_request = requests.get(solr_request_url)
      solr_request_json = solr_request.json()
      lcc.log_info("Response from Solr: %s " % str(solr_request_json))
      check_that("The assembly is indexed in docv2 collection in Solr", solr_request_json["response"]["numFound"],
                 equal_to(1))
      check_that("The content type", solr_request_json["response"]["docs"][0]["content_type"][0], equal_to("assembly"))
      check_that("The uri", solr_request_json["response"]["docs"][0]["uri"], equal_to(self.assembly_uuid))

    @lcc.disabled()
    @lcc.test("Verify if the assembly is available for search in access collection")
    def verify_solr_access_collection_assembly(self):
      time.sleep(40)
      solr_request_url = fixture.solr_url + "solr/access/select?indent=on&q=id:" + self.assembly_uuid + "&wt=json"
      lcc.log_info("Checking access collection in Solr: %s" % solr_request_url)
      solr_request = requests.get(solr_request_url)
      time.sleep(10)
      solr_request = requests.get(solr_request_url)
      solr_request_json = solr_request.json()
      lcc.log_info("Response from Solr: %s " % str(solr_request_json))
      check_that("The assembly is indexed in access collection in Solr", solr_request_json["response"]["numFound"],
                 equal_to(1))
      #add more checks here.
      check_that("The content type source ", solr_request_json["response"]["docs"][0]["source"], equal_to("assembly"))

    @lcc.test("Verify that the assembly is successfully unpublished, Hydra sends an ACK")
    def unpublish_assembly(self, api_auth):
      unpublish_url = fixture.url + self.path_for_assembly
      lcc.log_info("Unpublishing the assembly: %s" % unpublish_url)
      payload = {
        ":operation": "pant:unpublish",
        "locale": "en_US",
        "variant": self.variant
      }
      unpublish_assembly_request = self.api_auth.post(unpublish_url, data=payload, headers={'Accept': 'application/json'})
      time.sleep(12)
      check_that("Unpublish request status code", unpublish_assembly_request.status_code, equal_to(200))

      # Check if the unpublish request response does not return "url" for Customer Portal: CCS-3860
      cp_url_returned = unpublish_assembly_request.json()["location"]
      check_that("UnPublish Assembly response does not contain The Customer Portal URL", cp_url_returned,
                 not_(contains_string(fixture.cp_url + "documentation")))
      time.sleep(20)
      response = api_auth.get(self.request_url)
      lcc.log_info("Checking for ack_status at url after unpublish: %s" % str(self.request_url))
      check_that("The unpublished assembly now has a draft node with ack_status node ",
                 response.json()["en_US"]["variants"][self.variant]["draft"], has_entry("ack_status"))
      lcc.log_info(
        "Ack status node response: %s" % str(response.json()["en_US"]["variants"][self.variant]["draft"]["ack_status"]))
      # this is a place holder check
      check_that("The unpublished assembly has a successful message from Hydra",
                 response.json()["en_US"]["variants"][self.variant]["draft"]["ack_status"]["pant:message"],
                 equal_to("Solr call for delete was successful"))

      check_that("The unpublished assembly has a successful ACK from Hydra",
                 response.json()["en_US"]["variants"][self.variant]["draft"]["ack_status"]["pant:status"],
                 equal_to("SUCCESSFUL"))

    @lcc.test("Verify if the assembly is successfully removed from docv2 collection")
    def removed_from_docv2_Solr(self):
      time.sleep(15)
      solr_request_url = fixture.solr_url + "solr/docv2/select?indent=on&q=id:" + self.assembly_uuid + "&wt=json"
      lcc.log_info("Checking docv2 collection in Solr: %s" % solr_request_url)
      solr_request = requests.get(solr_request_url)
      time.sleep(5)
      solr_request = requests.get(solr_request_url)
      solr_request_json = solr_request.json()
      lcc.log_info("Response from Solr: %s " % str(solr_request_json))
      check_that("The assembly is removed from docv2 collection in Solr", solr_request_json["response"]["numFound"],
                 equal_to(0))

    @lcc.disabled()
    @lcc.test("Verify is the assembly is successfully removed from access collection in Solr")
    def removed_from_access_Solr(self):
      lcc.log_info("Checking if the assembly is removed from search results, access collection")
      time.sleep(20)
      solr_request_url = fixture.solr_url + "solr/access/select?indent=on&q=id:" + self.assembly_uuid + "&wt=json"
      lcc.log_info("Checking access collection in Solr: %s" % solr_request_url)
      solr_request = requests.get(solr_request_url)
      solr_request_json = solr_request.json()
      lcc.log_info("Response from Solr: %s " % str(solr_request_json))
      check_that("The assembly is removed from access collection in Solr", solr_request_json["response"]["numFound"],
                 equal_to(0))
