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
import suites.test_module_edit_publish as test_module_edit_publish

sys.path.append("..")

module_title_prefix = base.config_reader('test_repo', 'module_prefix')
module_prefix = base.config_reader('test_repo', 'module_content_prefix')
repo_name = base.config_reader('test_repo', 'repo_name')
assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')


@lcc.suite(description="Suite: Verify contents of published module", rank=2)
class test_module_content:
  api_auth = lcc.inject_fixture("api_auth")

  path_for_module = ""
  request_url = ""

  @lcc.test("Verify response of module variant api")
  def verify_module_content(self, api_auth, setup_test_products):
      #publishing related assembly
      self.variant = utilities.read_variant_name_from_pantheon2config()
      lcc.log_info(str(self.variant))
      self.variant = str(self.variant)
      self.path_for_assembly = utilities.select_nth_item_from_search_results(0, fixture.url, assembly_title_prefix)
      if "/modules" in self.path_for_assembly:
          self.path_for_assembly = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_title_prefix)
      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_assembly, self.variant, api_auth,
                                                     setup_test_products, content_type="assembly")
      # print(res.content)
      utilities.publish_content(fixture.url, self.path_for_assembly, self.variant, api_auth)

      assembly_uuid = utilities.fetch_uuid(fixture.url, self.path_for_assembly, self.variant)
      published_assembly_url = fixture.url + "api/assembly/variant.json/" + assembly_uuid
      print("published assembly url: \n" + published_assembly_url)
      lcc.log_info("Published Assembly api endpoint: %s" % published_assembly_url)
      data_from_published_assembly = api_auth.get(published_assembly_url)


      self.path_for_module = utilities.select_nth_item_from_search_results(0, fixture.url, module_prefix)
      if "/assemblies" in self.path_for_module:
          self.path_for_module = utilities.select_nth_item_from_search_results(1, fixture.url, module_prefix)
      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_module, self.variant, api_auth,
                                                     setup_test_products, content_type="module")
      # print(res.content)
      utilities.publish_content(fixture.url,self.path_for_module, self.variant, api_auth)

      module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant)
      published_module_url = fixture.url + "api/module/variant.json/" + module_uuid
      print("published module url: \n" + published_module_url)
      lcc.log_info("Published Module api endpoint: %s" % published_module_url)
      data_from_published_module = api_auth.get(published_module_url)
      check_that("The /api/module/variant.json/<module_uuid> endpoint for a published module",
                 data_from_published_module.status_code, equal_to(200))

      # print("Response from published module API endpoint: \n" + str(data_from_published_module.content))
      check_that("The response is ", data_from_published_module.json()["message"], equal_to("Module Found"))
      check_that("The title of the module ", data_from_published_module.json()["module"]["title"],
                 contains_string(module_prefix))
      check_that("The status of the module ", data_from_published_module.json()["module"]["status"],
                 equal_to("published"))
      check_that("The variant uuid of the module", data_from_published_module.json()["module"]["variant_uuid"],
                 equal_to(module_uuid))
      check_that("The uuid of the module", data_from_published_module.json()["module"]["uuid"], equal_to(module_uuid))
      check_that("The abstract of the module", data_from_published_module.json()["module"]["description"],
                 is_not_none())
      keywords = constants.searchKeywords.split(',')
      print(keywords)
      check_that("Search keywords", data_from_published_module.json()["module"]["search_keywords"], has_items(keywords))
      check_that("The module type", data_from_published_module.json()["module"]["content_type"], equal_to("module"))
      #date_published and #date_modified test pending
      path = self.path_for_module.split("repositories/")[1]
      path = path + "/en_US/variants/" + self.variant
      check_that("The module url fragment", data_from_published_module.json()["module"]["module_url_fragment"],
                 equal_to(path))
      check_that("The view_uri", data_from_published_module.json()["module"]["view_uri"], equal_to(
          fixture.cp_url + "documentation/en-us/topic/" + product_name_uri + "/" + constants.product_version_uri + "/" + module_uuid))
      check_that("The revision_id", data_from_published_module.json()["module"]["revision_id"], equal_to("released"))
      # print(data_from_published_module.json()["module"]["products"][0]["product_name"])
      check_that("The product name url", data_from_published_module.json()["module"]["products"][0]["product_url_fragment"],
                 equal_to(product_name_uri))
      check_that("The product version", data_from_published_module.json()["module"]["products"][0]["product_version"],
                 equal_to(constants.product_version))
      print(data_from_published_module.json()["module"]["included_in_guides"])
      count = len(data_from_published_module.json()["module"]["included_in_guides"])
      check_that("Number of guides included in", count, greater_than_or_equal_to(1))
      for i in range(count):
          check_that("Included in guides", data_from_published_module.json()["module"]["included_in_guides"][i]["title"],
                     contains_string(assembly_title_prefix))
      is_part_of_count = len(data_from_published_module.json()["module"]["isPartOf"])
      check_that("Is part of count", is_part_of_count, greater_than_or_equal_to(1))
      for i in range(is_part_of_count):
          check_that("Is part of", data_from_published_module.json()["module"]["isPartOf"][i]["title"],
                     contains_string(assembly_title_prefix))


