import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from helpers import utilities
from helpers import constants
import time
import requests
from fixtures import fixture
from polling2 import poll

git_import_repo_URL = base.config_reader('git_import_test_repo', 'git_import_repo_url')
git_import_repo_Name = base.config_reader('git_import_test_repo', 'git_import_repo_name')
git_import_repo_branch = base.config_reader('git_import_test_repo', 'git_import_repo_branch')
number_of_modules = base.config_reader('git_import_test_repo', 'number_of_modules_imported')
module_title_prefix = base.config_reader('git_import_test_repo', 'module_prefix')
assembly_title_prefix = base.config_reader('git_import_test_repo', 'assembly_prefix')


@lcc.suite("Suite: Git import functionality", rank=3)
class test_git_import:

  @lcc.test("Verify that git import API is able to git import modules successfully")
  def git_import_api(self):
    lcc.log_info("Checking for post request to git import functionality...")
    payload = {
              "branch": git_import_repo_branch,
              "repo": git_import_repo_URL
            }
    git_import_req = requests.post(fixture.git_import_server + "/clone", data=payload)
    time.sleep(30)
    check_that("POST request to git import was done", git_import_req.status_code, equal_to(200))

    search_url = fixture.url + 'pantheon/internal/modules.json?search=' + module_title_prefix
    lcc.log_info("Git import functionality verified using endpoint: %s" % search_url)
    lcc.log_info("Trying to poll the endpoint until we get the required number of search results as"
                 " per the test data ...")

    imported_modules_array = []

    def check_if_imported(response):
      result1 = response.json()["results"]
      for result in result1:
        print("list of results found")
        print(result1["size"])
        if result["pant:transientSourceName"] == git_import_repo_Name:
          imported_modules_array.append(result["jcr:title"])
          print("found matching result")
        else:
          print("No matching result found yet")
          time.sleep(2)
      return len(imported_modules_array) == int(number_of_modules)

    poll(lambda: requests.get(search_url), check_success=check_if_imported, step=5, timeout=150 )

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



