import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from helpers import utilities
from helpers import constants
import time
import requests
import json
from fixtures import fixture
from polling2 import poll

git_import_repo_URL = base.config_reader('git_import_test_repo', 'git_import_repo_url')
git_import_repo_Name = base.config_reader('git_import_test_repo', 'git_import_repo_name')
git_import_repo_branch = base.config_reader('git_import_test_repo', 'git_import_repo_branch')
number_of_modules = base.config_reader('git_import_test_repo', 'number_of_modules_imported')
module_title_prefix = base.config_reader('git_import_test_repo', 'module_prefix')
assembly_title_prefix = base.config_reader('git_import_test_repo', 'assembly_prefix')
number_of_resources_uploaded = base.config_reader('git_import_test_repo', 'number_of_resources_uploaded')

@lcc.suite(description="Suite: Git import functionality", rank=6)
class test_git_import:
    api_auth = lcc.inject_fixture("api_auth")

    # @lcc.disabled()
    @lcc.test("Verify that git import API is able to git import modules successfully")
    def git_import_api(self):
        lcc.log_info("Checking for post request to git import functionality...")
        payload = {
            "branch": git_import_repo_branch,
            "repo": git_import_repo_URL
        }

        payload = json.dumps(payload)
        lcc.log_info(str(payload))
        git_import_req = requests.post(fixture.git_import_server + "/api/clone", data=payload)
        lcc.log_info(git_import_req.url)
        time.sleep(15)
        print("Response code for git import request:" + str(git_import_req.status_code))
        print(git_import_req.content)

        # print("Response json: " + str(git_import_req.json()))
        require_that("POST request to git import was done", git_import_req.status_code, equal_to(202))
        git_clone_response = git_import_req.content

        # search_url = fixture.url + 'pantheon/internal/modules.json?search=' + module_title_prefix
        # lcc.log_info("Git import functionality verified using endpoint: %s" % search_url)
        # lcc.log_info("Trying to poll the endpoint until we get the required number of search results as"
        #              " per the test data ...")
        #
        # imported_modules_array = []
        #
        # def check_if_imported(response):
        #     time.sleep(2)
        #     print("Response code for 'search' api request: " + str(response.status_code))
        #     result1 = response.json()["results"]
        #     lcc.log_info(
        #         "list of results found in total but not specific to this request: %s" % str(response.json()["size"]))
        #     print("Number of results found which were uploaded for git import: " + str(response.json()["size"]))
        #     for result in result1:
        #         if result["pant:transientSourceName"] == git_import_repo_Name:
        #             imported_modules_array.append(result["jcr:title"])
        #             print("Found a matching result, waiting for more...")
        #
        #         else:
        #             print("No matching result found yet...")
        #             time.sleep(2)
        #     check_that("Count of modules uploaded using git import", len(imported_modules_array),
        #                greater_than_or_equal_to(int(number_of_modules)))
        #     return len(imported_modules_array) >= int(number_of_modules)

        # poll(lambda: requests.get(search_url), check_success=check_if_imported, step=5, timeout=60)

        git_status_res = requests.post(fixture.git_import_server + "/api/status", data=git_clone_response)
        require_that("POST request to git resources was done", git_status_res.status_code, equal_to(200))
        print(str(git_status_res.content))

        def check_current_status(response):
            json_response = response.json()
            current_status = json_response["current_status"]
            lcc.log_info(current_status)
            return current_status == "done"

        poll(lambda: requests.post(fixture.git_import_server + "/api/progress-update/resources", data=git_clone_response),
                        check_success=check_current_status, step=2, timeout=10)

        poll(lambda: requests.post(fixture.git_import_server + "/api/progress-update/modules",data=git_clone_response,
             check_success=check_current_status, step=2, timeout=10))

        poll(lambda: requests.post(fixture.git_import_server + "/api/progress-update/assemblies",data=git_clone_response,
             check_success=check_current_status, step=2, timeout=10))




        # require_that("POST request to progress update resources was done", progress_update_resources_res.status_code,
        #              equal_to(200))
        #
        # progress_update_res = requests.post(fixture.git_import_server + "/api/progress-update/all",
        #                                     data=git_clone_response)
        # require_that("POST request to progress update was done", progress_update_res.status_code, equal_to(200))
        # lcc.log_info("progress update response:" + str(progress_update_res.content))
        #
        # progress_update_assemblies_res = requests.post(fixture.git_import_server + "/api/progress-update/assemblies",
        #                                                data=git_clone_response)
        # require_that("POST request to progress update assemblies was done", progress_update_assemblies_res.status_code,
        #              equal_to(200))
        # lcc.log_info("progress update assembly response:" + str(progress_update_assemblies_res.content))
        #
        # progress_update_modules_res = requests.post(fixture.git_import_server + "/api/progress-update/modules",
        #                                             data=git_clone_response)
        # require_that("POST request to progress update modules was done", progress_update_modules_res.status_code,
        #              equal_to(200))
        # lcc.log_info("progress update modules response:" + str(progress_update_modules_res.content))
        #
        #
        # lcc.log_info("progress update resources response:" + str(progress_update_resources_res.content))

    def teardown_suite(self):
        # Deleting the git repo uploaded via git import in the test suite.
        lcc.log_info("Deleting the git repo imported...")
        path_to_git_repo = fixture.url + "bin/cpm/nodes/node.json/content/repositories/" + git_import_repo_Name
        lcc.log_info("Test repo node used for git import functionality being deleted at: %s" % path_to_git_repo)
        response_git_delete = requests.delete(path_to_git_repo, auth=(fixture.admin_username, fixture.admin_auth))
        print(str(response_git_delete.content))
        check_that("The git import test repo was deleted successfully from backend", response_git_delete.status_code,
                   equal_to(200))
