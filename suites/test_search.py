import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll

sys.path.append("..")

git_import_repo_URL = base.config_reader('git_import_test_repo', 'git_import_repo_url')
git_import_repo_Name = base.config_reader('git_import_test_repo', 'git_import_repo_name')
git_import_repo_branch = base.config_reader('git_import_test_repo', 'git_import_repo_branch')
number_of_modules = base.config_reader('git_import_test_repo', 'number_of_modules_imported')
#module_title_prefix = constants.module_title_prefix


@lcc.suite("Suite: Verify search functionality", rank="1")
class test_search():
  api_auth = lcc.inject_fixture("api_auth")

  @lcc.test("Verify that the recently uploaded modules are present in search results")
  def search(self):
    lcc.log_info("Making a search request for prefix: API test module")
    search_request = requests.get(fixture.url + "pantheon/internal/modules.json?search=" +
                                  base.config_reader('test_repo', 'module_prefix'))
    print(search_request.json())
    search_results = search_request.json()
    number_of_results = search_results["size"]

    lcc.log_info(str(search_request.status_code))
    lcc.log_info(str(search_request.json()))


    lcc.log_info("Git import functionality verified using endpoint: %s" % search_url)
    lcc.log_info("Trying to poll the endpoint until we get the required number of search results as"
                 " per the test data ...")
    poll(lambda: requests.get(search_url).json()["size"] == 9, step=5, timeout=120)

    imported_modules_request = requests.get(search_url)
    imported_modules = imported_modules_request.json()
    lcc.log_info(str(imported_modules))
    total_modules = imported_modules["size"]

    lcc.log_info("Number of modules listed with the similar title name: %s" % str(total_modules))
    lcc.log_info("Capturing the number of modules uploaded from the repo: %s ..." % git_import_repo_Name)
    results = imported_modules["results"]
    imported_modules_array = []
    for result in results:
      if result["pant:transientSourceName"] == git_import_repo_Name:
        imported_modules_array.append(result["jcr:title"])
    lcc.log_info("Modules imported successfully via git import: %s with title prefix" % str(imported_modules_array))
    lcc.log_info("Number of modules imported successfully from repo: %s is %s" % (git_import_repo_URL,
                                                                                  str(len(imported_modules_array))))
    check_that("Count of modules uploaded using git import", len(imported_modules_array),
               equal_to(int(number_of_modules)))
