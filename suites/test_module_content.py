import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from html2json import collect
from urllib.parse import urlparse
from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll
from helpers import utilities
import urllib.parse
import suites.test_module_edit_publish as test_module_edit_publish
import os
import subprocess
import time

proxy_server = base.config_reader('proxy', 'proxy_server')

proxies = {
    "http": proxy_server,
    "https": proxy_server,
}

sys.path.append("..")

module_title_prefix = base.config_reader('test_repo', 'module_prefix')
module_prefix = base.config_reader('test_repo', 'module_content_prefix')
repo_name = base.config_reader('test_repo', 'repo_name')
assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')
assembly_prefix = base.config_reader('test_repo', 'assembly_content_prefix')
env = os.getenv('PANTHEON_ENV')
cp_url = base.config_reader(env,'cp_url')
cp_pantheon_url = base.config_reader(env, 'cp_pantheon_api')
proxy_url = base.config_reader(env, 'ext_proxy_url')
proxy_server = base.config_reader('proxy', 'proxy_server')

@lcc.suite(description="Suite: Verify contents of published module", rank=2)
class test_module_content:
  api_auth = lcc.inject_fixture("api_auth")

  path_for_module = ""
  request_url = ""

  @lcc.test("Verify response of module variant api also verify external proxy url, pantheon URL and CP url resolve imageassets correctly")
  def verify_module_content(self, api_auth, setup_test_products):
      #publishing related assembly
      self.variant = utilities.read_variant_name_from_pantheon2config()
      lcc.log_info(str(self.variant))
      self.variant = str(self.variant)
      lcc.log_info("In order to verify content for a module, publishing a related assembly...")
      self.path_for_assembly = utilities.select_nth_item_from_search_results(0, fixture.url, assembly_title_prefix, api_auth)

      if "/modules" in self.path_for_assembly:
          self.path_for_assembly = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_title_prefix, api_auth)

      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_assembly, self.variant, api_auth,
                                                     setup_test_products, content_type="assembly")
      check_that("Edit metadata request response for the above assembly", res.status_code, equal_to(200))
      lcc.log_info("Edit metadata response content: %s" % str(res.content))

      publish_req_assembly = utilities.publish_content(fixture.url, self.path_for_assembly, self.variant, api_auth)
      check_that("Expect the above assembly to be published, response code ", publish_req_assembly.status_code, equal_to(200))
      lcc.log_info("Publish assembly response content: %s" % str(publish_req_assembly.content))

      assembly_uuid = utilities.fetch_uuid(fixture.url, self.path_for_assembly, self.variant,api_auth)
      published_assembly_url = fixture.url + "api/assembly/variant.json/" + assembly_uuid
      published_assembly_relative_url = "api/assembly/variant.json/" + assembly_uuid
      print("published assembly url: \n" + published_assembly_url)
      lcc.log_info("Published Assembly api endpoint: %s" % published_assembly_url)
      data_from_published_assembly = api_auth.get(published_assembly_url)


      self.path_for_module = utilities.select_nth_item_from_search_results(0, fixture.url, module_prefix, api_auth)
      if "/assemblies" in self.path_for_module:
          self.path_for_module = utilities.select_nth_item_from_search_results(1, fixture.url, module_prefix,api_auth)
      res, product_name_uri = utilities.add_metadata(fixture.url, self.path_for_module, self.variant, api_auth,
                                                     setup_test_products, content_type="module")
      lcc.log_info("Publishing a module now to test for included content: %s" % self.path_for_module)

      publish_req_module = utilities.publish_content(fixture.url,self.path_for_module, self.variant, api_auth)

      check_that("Module has been published ", publish_req_module.status_code, equal_to(200))
      module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant,api_auth)
      published_module_url = fixture.url + "api/module/variant.json/" + module_uuid
      # print("published module url: \n" + published_module_url)
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
          fixture.cp_url + "documentation/en-us/" + product_name_uri + "/" + constants.product_version_uri + "/topic/" + module_uuid))

      check_that("The revision_id", data_from_published_module.json()["module"]["revision_id"], equal_to("released"))
      # print(data_from_published_module.json()["module"]["products"][0]["product_name"])
      check_that("The product name url", data_from_published_module.json()["module"]["products"][0]["product_url_fragment"],
                 equal_to(product_name_uri))
      check_that("The product version", data_from_published_module.json()["module"]["products"][0]["product_version"],
                 equal_to(constants.product_version))
      lcc.log_info("Included in guides from the API response: %s" % str(data_from_published_module.json()["module"]["included_in_guides"]))
      count = len(data_from_published_module.json()["module"]["included_in_guides"])
      check_that("Number of guides included in", count, greater_than_or_equal_to(1))
      relative_url = []
      for i in range(count):
          print(data_from_published_module.json()["module"]["included_in_guides"][i]["relative_url"])
          relative_url.append(data_from_published_module.json()["module"]["included_in_guides"][i]["relative_url"])
          check_that("Included in guides", data_from_published_module.json()["module"]["included_in_guides"][i]["title"],
                     contains_string(assembly_title_prefix) or contains_string(assembly_prefix))
          check_that("Included in guides data", data_from_published_module.json()["module"]["included_in_guides"][i],
                     all_of(has_entry("title"), has_entry("uuid"), has_entry("url"), has_entry("view_uri"),
                            has_entry("relative_url"), has_entry("pantheon_env")))
          check_that("Included in guides-> pantheon_env",
                     data_from_published_module.json()["module"]["included_in_guides"][i]["pantheon_env"],
                     equal_to(env))
      print(*relative_url)
      check_that("Relative url to", relative_url, has_item("/"+published_assembly_relative_url))
      is_part_of_content = data_from_published_module.json()["module"]["isPartOf"]
      lcc.log_info("Is part of content from the API response: %s " % str(is_part_of_content))
      is_part_of_count = len(data_from_published_module.json()["module"]["isPartOf"])
      check_that("Is part of count", is_part_of_count, greater_than_or_equal_to(1))
      relative_url1 = []
      for i in range(is_part_of_count):
          print(data_from_published_module.json()["module"]["isPartOf"][i]["relative_url"])
          relative_url1.append(data_from_published_module.json()["module"]["isPartOf"][i]["relative_url"])
          check_that("Is part of", data_from_published_module.json()["module"]["isPartOf"][i]["title"],
                     contains_string(assembly_title_prefix) or contains_string(assembly_prefix))
          check_that("isPartOf data", data_from_published_module.json()["module"]["isPartOf"][i],
                     all_of(has_entry("title"), has_entry("uuid"), has_entry("url"), has_entry("view_uri"),
                            has_entry("relative_url"), has_entry("pantheon_env")))
          check_that("isPartOf-> pantheon_env",
                     data_from_published_module.json()["module"]["isPartOf"][i]["pantheon_env"], equal_to(env))
      print(*relative_url1)
      check_that("Relative url to", relative_url1, has_item("/"+published_assembly_relative_url))

      time.sleep(10)
      # Test to verify external proxy url, pantheon URL and CP url resolve image assets correctly
      proxies = {
          "http": proxy_server,
          "https": proxy_server,
      }
      body = data_from_published_module.json()["module"]["body"]
      src = collect(body,{"Path": ["img", "src", []]})
      path = (src["Path"]).lstrip("/")
      print(cp_url+path)
      resp1 = requests.get(cp_url+path, proxies=proxies)
      print(cp_pantheon_url + path)
      resp2 = requests.get(cp_pantheon_url + path, proxies=proxies)
      print(proxy_url+path)
      resp3 = requests.get(proxy_url+path, proxies=proxies)

      check_that("Imageassets for url behind akamai", resp1.status_code, equal_to(200))
      check_that("Imageassets for Pantheon url", resp2.status_code, equal_to(200))
      check_that("Imageassets for external proxy url", resp3.status_code, equal_to(200))


  @lcc.test("Verify response of module variant api behind akamai")
  def verify_module_content_behind_akamai_endpoints(self, api_auth, setup_test_products):
      module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant, api_auth)
      published_module_url = fixture.behind_akamai_url + "api/module/variant.json/" + module_uuid
      # print("published module url: \n" + published_module_url)
      lcc.log_info("Published Module api endpoint: %s" % published_module_url)
      data_from_published_module = api_auth.get(published_module_url, proxies= proxies)
      check_that("The /api/module/variant.json/<module_uuid> endpoint for a published module",
                 data_from_published_module.status_code, equal_to(200))

      lcc.log_info("Response from published module API endpoint: \n" + str(data_from_published_module.content))
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
      # date_published and #date_modified test pending
      path = self.path_for_module.split("repositories/")[1]
      path = path + "/en_US/variants/" + self.variant
      check_that("The module url fragment", data_from_published_module.json()["module"]["module_url_fragment"],
                 equal_to(path))
      check_that("The revision_id", data_from_published_module.json()["module"]["revision_id"], equal_to("released"))
      check_that("The product version", data_from_published_module.json()["module"]["products"][0]["product_version"],
                 equal_to(constants.product_version))
      lcc.log_info("Included in guides from the API response: %s" % str(
          data_from_published_module.json()["module"]["included_in_guides"]))
      count = len(data_from_published_module.json()["module"]["included_in_guides"])
      check_that("Number of guides included in", count, greater_than_or_equal_to(1))
      relative_url = []
      for i in range(count):
          print(data_from_published_module.json()["module"]["included_in_guides"][i]["relative_url"])
          relative_url.append(data_from_published_module.json()["module"]["included_in_guides"][i]["relative_url"])
          check_that("Included in guides",
                     data_from_published_module.json()["module"]["included_in_guides"][i]["title"],
                     contains_string(assembly_title_prefix) or contains_string(assembly_prefix))
          check_that("Included in guides data", data_from_published_module.json()["module"]["included_in_guides"][i],
                     all_of(has_entry("title"), has_entry("uuid"), has_entry("url"), has_entry("view_uri"),
                            has_entry("relative_url"), has_entry("pantheon_env")))
          check_that("Included in guides-> pantheon_env",
                     data_from_published_module.json()["module"]["included_in_guides"][i]["pantheon_env"],
                     equal_to(env))
      is_part_of_content = data_from_published_module.json()["module"]["isPartOf"]
      lcc.log_info("Is part of content from the API response: %s " % str(is_part_of_content))
      is_part_of_count = len(data_from_published_module.json()["module"]["isPartOf"])
      check_that("Is part of count", is_part_of_count, greater_than_or_equal_to(1))
      relative_url1 = []
      for i in range(is_part_of_count):
          print(data_from_published_module.json()["module"]["isPartOf"][i]["relative_url"])
          relative_url1.append(data_from_published_module.json()["module"]["isPartOf"][i]["relative_url"])
          check_that("Is part of", data_from_published_module.json()["module"]["isPartOf"][i]["title"],
                     contains_string(assembly_title_prefix) or contains_string(assembly_prefix))
          check_that("isPartOf data", data_from_published_module.json()["module"]["isPartOf"][i],
                     all_of(has_entry("title"), has_entry("uuid"), has_entry("url"), has_entry("view_uri"),
                            has_entry("relative_url"), has_entry("pantheon_env")))
          check_that("isPartOf-> pantheon_env",
                     data_from_published_module.json()["module"]["isPartOf"][i]["pantheon_env"], equal_to(env))

  @lcc.test("Verify response of module variant api for external proxy API")
  def verify_module_content_ext_proxy(self, api_auth, setup_test_products):
      module_uuid = utilities.fetch_uuid(fixture.url, self.path_for_module, self.variant, api_auth)
      published_module_url = fixture.external_proxy_url + "module/variant.json/" + module_uuid
      # print("published module url: \n" + published_module_url)
      lcc.log_info("Published Module api endpoint: %s" % published_module_url)
      data_from_published_module = api_auth.get(published_module_url, proxies=proxies)
      check_that("The /api/module/variant.json/<module_uuid> endpoint for a published module",
                 data_from_published_module.status_code, equal_to(200))

      lcc.log_info("Response from published module API endpoint: \n" + str(data_from_published_module.content))
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
      # date_published and #date_modified test pending
      path = self.path_for_module.split("repositories/")[1]
      path = path + "/en_US/variants/" + self.variant
      check_that("The module url fragment", data_from_published_module.json()["module"]["module_url_fragment"],
                 equal_to(path))
      check_that("The revision_id", data_from_published_module.json()["module"]["revision_id"], equal_to("released"))
      check_that("The product version", data_from_published_module.json()["module"]["products"][0]["product_version"],
                 equal_to(constants.product_version))
      lcc.log_info("Included in guides from the API response: %s" % str(
          data_from_published_module.json()["module"]["included_in_guides"]))
      count = len(data_from_published_module.json()["module"]["included_in_guides"])
      check_that("Number of guides included in", count, greater_than_or_equal_to(1))
      relative_url = []
      for i in range(count):
          print(data_from_published_module.json()["module"]["included_in_guides"][i]["relative_url"])
          relative_url.append(data_from_published_module.json()["module"]["included_in_guides"][i]["relative_url"])
          check_that("Included in guides",
                     data_from_published_module.json()["module"]["included_in_guides"][i]["title"],
                     contains_string(assembly_title_prefix) or contains_string(assembly_prefix))
          check_that("Included in guides data", data_from_published_module.json()["module"]["included_in_guides"][i],
                     all_of(has_entry("title"), has_entry("uuid"), has_entry("url"), has_entry("view_uri"),
                            has_entry("relative_url"), has_entry("pantheon_env")))
          check_that("Included in guides-> pantheon_env",
                     data_from_published_module.json()["module"]["included_in_guides"][i]["pantheon_env"],
                     equal_to(env))
      is_part_of_content = data_from_published_module.json()["module"]["isPartOf"]
      lcc.log_info("Is part of content from the API response: %s " % str(is_part_of_content))
      is_part_of_count = len(data_from_published_module.json()["module"]["isPartOf"])
      check_that("Is part of count", is_part_of_count, greater_than_or_equal_to(1))
      relative_url1 = []
      for i in range(is_part_of_count):
          print(data_from_published_module.json()["module"]["isPartOf"][i]["relative_url"])
          relative_url1.append(data_from_published_module.json()["module"]["isPartOf"][i]["relative_url"])
          check_that("Is part of", data_from_published_module.json()["module"]["isPartOf"][i]["title"],
                     contains_string(assembly_title_prefix) or contains_string(assembly_prefix))
          check_that("isPartOf data", data_from_published_module.json()["module"]["isPartOf"][i],
                     all_of(has_entry("title"), has_entry("uuid"), has_entry("url"), has_entry("view_uri"),
                            has_entry("relative_url"), has_entry("pantheon_env")))
          check_that("isPartOf-> pantheon_env",
                     data_from_published_module.json()["module"]["isPartOf"][i]["pantheon_env"], equal_to(env))
