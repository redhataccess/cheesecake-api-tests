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
import os

sys.path.append("..")

assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')
assembly_prefix = base.config_reader('test_repo', 'assembly_content_prefix')
repo_name = base.config_reader('test_repo', 'repo_name')
module_title_prefix = base.config_reader('test_repo', 'module_prefix')
env = os.getenv('PANTHEON_ENV')


@lcc.suite(description="Suite: Verify contents of published assembly", rank=4)
class test_assembly_content:
  api_auth = lcc.inject_fixture("api_auth")

  path_for_assembly = ""
  request_url = ""

  @lcc.test("Verify response of assembly variant api")
  def verify_assembly_content(self, api_auth, setup_test_products):
      #Publishing module included in assembly
      self.variant = utilities.read_variant_name_from_pantheon2config()
      lcc.log_info(str(self.variant))
      self.variant = str(self.variant)
      self.path_for_module = utilities.select_nth_item_from_search_results(0, fixture.url, module_title_prefix + " Include", api_auth)
      if "/assemblies" in self.path_for_module:
          self.path_for_module = utilities.select_nth_item_from_search_results(2, fixture.url, module_title_prefix, api_auth)
      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_module, self.variant, api_auth,
                                                     setup_test_products, content_type="module")
      utilities.publish_content(fixture.url, self.path_for_module, self.variant, api_auth)

      module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant, api_auth)
      published_module_url = fixture.url + "api/module/variant.json/" + module_uuid
      published_module_relative_url = "api/module/variant.json/" + module_uuid
      print("published module url: \n" + published_module_url)
      lcc.log_info("Published Module api endpoint: %s" % published_module_url)
      data_from_published_module = api_auth.get(published_module_url)
      print(data_from_published_module.json())

      self.path_for_assembly = utilities.select_nth_item_from_search_results(0, fixture.url, assembly_prefix, api_auth)
      if "/modules" in self.path_for_assembly:
          self.path_for_assembly = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_prefix, api_auth)
      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_assembly, self.variant, api_auth,
                                                     setup_test_products, content_type="assembly")
      # print(res.content)
      utilities.publish_content(fixture.url,self.path_for_assembly, self.variant, api_auth)

      assembly_uuid = utilities.fetch_uuid(fixture.url, self.path_for_assembly, self.variant, api_auth)
      published_assembly_url = fixture.url + "api/assembly/variant.json/" + assembly_uuid
      print("published assembly url: \n" + published_assembly_url)
      lcc.log_info("Published Assembly api endpoint: %s" % published_assembly_url)
      data_from_published_assembly = api_auth.get(published_assembly_url)
      print(data_from_published_assembly.content)
      check_that("The /api/assembly/variant.json/<assembly_uuid> endpoint for a published assembly",
                 data_from_published_assembly.status_code, equal_to(200))

      # print("Response from published assembly API endpoint: \n" + str(data_from_published_assembly.content))
      check_that("The response is ", data_from_published_assembly.json()["message"], equal_to("Assembly Found"))
      check_that("The title of the assembly ", data_from_published_assembly.json()["assembly"]["title"],
                 contains_string(assembly_prefix))
      check_that("The status of the assembly ", data_from_published_assembly.json()["assembly"]["status"],
                 equal_to("published"))
      # check_that("The uuid of the assembly", data_from_published_assembly.json()["assembly"]["uuid"],
      #            equal_to(assembly_uuid))
      check_that("The uuid of the assembly", data_from_published_assembly.json()["assembly"]["uuid"],
                 equal_to(assembly_uuid))
      check_that("The abstract of the assembly", data_from_published_assembly.json()["assembly"]["description"],
                 equal_to(constants.assembly_abstract))
      keywords = constants.assembly_searchkeywords.split(',')
      print(keywords)
      all_of(check_that("Search keywords", data_from_published_assembly.json()["assembly"]["search_keywords"],
                        has_items(keywords)))
      check_that("The assembly type", data_from_published_assembly.json()["assembly"]["content_type"],
                 equal_to("assembly"))
      #date_published and #date_modified test pending
      path = self.path_for_assembly.split("repositories/")[1]
      path = path + "/en_US/variants/" + self.variant
      check_that("The assembly url fragment", data_from_published_assembly.json()["assembly"]["assembly_url_fragment"],
                 equal_to(path))
      check_that("The view_uri", data_from_published_assembly.json()["assembly"]["view_uri"], equal_to(
          fixture.cp_url + "documentation/en-us/" + product_name_uri + "/" + constants.product_version_uri + "/guide/" + assembly_uuid))
      check_that("The revision_id", data_from_published_assembly.json()["assembly"]["revision_id"], equal_to("released"))
      # print(data_from_published_assembly.json()["assembly"]["products"][0]["product_name"])
      check_that("The product name url", data_from_published_assembly.json()["assembly"]["products"][0]["product_url_fragment"],
                 equal_to(product_name_uri))
      check_that("The product version",
                 data_from_published_assembly.json()["assembly"]["products"][0]["product_version"],
                 equal_to(constants.product_version))
      lcc.log_info("Modules included from the API response: %s" % str(
          data_from_published_assembly.json()["assembly"]["modules_included"]))
      number_of_modules_included = len(data_from_published_assembly.json()["assembly"]["modules_included"])
      check_that("Number of Modules included", number_of_modules_included, greater_than_or_equal_to(1))
      relative_url = []
      for i in range(number_of_modules_included):
          print(data_from_published_assembly.json()["assembly"]["modules_included"][i]["relative_url"])
          relative_url.append(data_from_published_assembly.json()["assembly"]["modules_included"][i]["relative_url"])
          check_that("Modules included",
                     data_from_published_assembly.json()["assembly"]["modules_included"][i],
                     all_of(has_entry("canonical_uuid"), has_entry("level_offset"), has_entry("module_uuid"),
                            has_entry("title"), has_entry("url"), has_entry("pantheon_env"),
                            has_entry("relative_url")))
          check_that("Modules included-> pantheon_env",
                     data_from_published_assembly.json()["assembly"]["modules_included"][i]["pantheon_env"], equal_to(env))
      print(*relative_url)
      check_that("Relative url to", relative_url, has_item("/"+published_module_relative_url))
      lcc.log_info("hasPart from the API response: %s" % str(
          data_from_published_assembly.json()["assembly"]["hasPart"]))
      number_of_modules_hasPart = len(data_from_published_assembly.json()["assembly"]["hasPart"])
      check_that("Number of Modules in hasPart", number_of_modules_hasPart, greater_than_or_equal_to(1))
      relative_url1 = []
      for i in range(number_of_modules_hasPart):
          print(data_from_published_assembly.json()["assembly"]["hasPart"][i]["relative_url"])
          relative_url1.append(data_from_published_assembly.json()["assembly"]["hasPart"][i]["relative_url"])
          check_that("hasPart section ",
                     data_from_published_assembly.json()["assembly"]["hasPart"][i],
                     all_of(has_entry("canonical_uuid"), has_entry("level_offset"), has_entry("module_uuid"),
                            has_entry("title"), has_entry("url"), has_entry("pantheon_env"),
                            has_entry("relative_url")))
          any_of(check_that("hasPart-> pantheon_env",
                     data_from_published_assembly.json()["assembly"]["hasPart"][i]["pantheon_env"], equal_to(env)))
      print(*relative_url1)
      check_that("Relative url to", relative_url1, has_item("/"+published_module_relative_url))
