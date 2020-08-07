import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll


number_of_modules = base.config_reader('test_repo', 'number_of_modules_uploaded')
module_title_prefix = base.config_reader('test_repo', 'module_prefix')


@lcc.suite("Suite: Verify search functionality", rank=2)
class test_search:
  api_auth = lcc.inject_fixture("api_auth")

  @lcc.test("Verify that the recently uploaded modules are present in search results: %s" % module_title_prefix)
  def search(self):
    lcc.log_info("Making a search request for prefix: API test module")
    search_request = requests.get(fixture.url + "pantheon/internal/modules.json?search=" + module_title_prefix)
    print(search_request.json())
    search_results = search_request.json()
    number_of_results = search_results["size"]

    lcc.log_info(str(search_request.status_code))
    lcc.log_info(str(search_request.json()))
    check_that("Number of search results should be >= %s as per the test data; " % number_of_modules,
               int(number_of_results), greater_than_or_equal_to(int(number_of_results)))
