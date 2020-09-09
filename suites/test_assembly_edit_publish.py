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

sys.path.append("..")

assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')


@lcc.suite(description="Suite: Tests for Assemblies", rank=3)
class test_assembly_edit_publish:
    api_auth = lcc.inject_fixture("api_auth")
    global product_id

    @lcc.test("Verify that authenticated user can edit metadata for an assembly successfully")
    def verify_edit_metadata(self, setup_test_products):
        self.variant = utilities.read_variant_name_from_pantheon2config()
        lcc.log_info(str(self.variant))
        self.variant = str(self.variant)
        self.path_for_assembly = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_title_prefix)

        edit_metadata_url = fixture.url + "content/" + self.path_for_assembly + "/en_US/variants/" + \
                            self.variant + "/draft/metadata"
        lcc.log_info("Edit metadata request for assembly at : %s " % edit_metadata_url)

        # Fetch the product id from fixtures/fixtures.py, the test product and version was created as a setup step.
        product_id, product_name_uri = setup_test_products

        payload = {"productVersion": product_id,
                   "documentUsecase": constants.assembly_documentusecase,
                   "urlFragment": constants.assembly_urlfragment,
                   "searchKeywords": constants.assembly_searchkeywords}

        edit_metadata_request = self.api_auth.post(edit_metadata_url, data=payload)

        request_url = fixture.url + "content/" + self.path_for_assembly + ".7.json"
        time.sleep(10)

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
        print("Payload: ",payload)
        publish_url = fixture.url + "content/" + self.path_for_assembly
        print("\n API end point used for publish request: " + publish_url)
        time.sleep(10)
        publish_request = api_auth.post(publish_url, data=payload)
        print("\n Publish request response: \n" + str(publish_request.content))
        check_that("The publish request is successful", publish_request.status_code, equal_to(200))
        time.sleep(15)

        req = api_auth.get(fixture.url + "content/" + self.path_for_assembly + ".7.json")

        check_that("The status node in variants > variant >: ", req.json()["en_US"]["variants"][self.variant],
                   has_entry("released"), quiet=True)

        assembly_uuid = utilities.fetch_uuid(fixture.url, self.path_for_assembly, self.variant)

        published_assembly_url = fixture.url + "api/assembly/variant.json/" + assembly_uuid
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





