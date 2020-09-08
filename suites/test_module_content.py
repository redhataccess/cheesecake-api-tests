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
module_prefix = base.config_reader('test_repo', 'module_content_prefix')
repo_name = base.config_reader('test_repo', 'repo_name')


@lcc.suite(description="Suite: Verify contents of published module", rank=2)
class test_module_content:
  api_auth = lcc.inject_fixture("api_auth")

  path_for_module = ""
  request_url = ""

  @lcc.test("Verify that authenticated user can edit metadata successfully")
  def edit_metadata(self, api_auth, setup_test_products):
      self.variant = utilities.read_variant_name_from_pantheon2config()
      lcc.log_info(str(self.variant))
      self.variant = str(self.variant)
      self.path_for_module = utilities.select_first_item_from_search_results(fixture.url, module_prefix)
      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_module, self.variant, api_auth, setup_test_products, content_type="module")
      print(res.content)
      utilities.publish_content(fixture.url,self.path_for_module, self.variant, api_auth)

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
      check_that("The module url fragment", data_from_published_module.json()["module"]["module_url_fragment"], equal_to(path))
      check_that("The view_uri", data_from_published_module.json()["module"]["view_uri"], equal_to(
          fixture.cp_url + "documentation/en-us/topic/" + product_name_uri + "/" + constants.product_version_uri + "/" + module_uuid))
      check_that("The revision_id", data_from_published_module.json()["module"]["revision_id"], equal_to("released"))
      # print(data_from_published_module.json()["module"]["products"][0]["product_name"])
      check_that("The product name", data_from_published_module.json()["module"]["products"][0]["product_name"], contains_string(constants.product_name))
      check_that("The product version", data_from_published_module.json()["module"]["products"][0]["product_version"], equal_to(constants.product_version))
