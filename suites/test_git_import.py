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
# number_of_modules = base.config_reader('git_import_test_repo', 'number_of_modules_imported')
# module_title_prefix = base.config_reader('git_import_test_repo', 'module_prefix')
# assembly_title_prefix = base.config_reader('git_import_test_repo', 'assembly_prefix')
number_of_resources_uploaded = base.config_reader('git_import_test_repo', 'number_of_resources_uploaded')
number_of_modules_uploaded = base.config_reader('git_import_test_repo', 'number_of_modules_uploaded')
number_of_assemblies_uploaded = base.config_reader('git_import_test_repo', 'number_of_assemblies_uploaded')


@lcc.suite(description="Suite: Git import functionality", rank=6)
class test_git_import:
    api_auth = lcc.inject_fixture("api_auth")
    status_key = ""

    @lcc.test("Verify that git clone API is able to upload files successfully and get status_key from response")
    def git_clone_api(self):
        payload = {
            "branch": git_import_repo_branch,
            "repo": git_import_repo_URL
        }

        payload = json.dumps(payload)
        lcc.log_info(str(payload))
        git_import_req = requests.post(fixture.git_import_server + "/api/clone", data=payload)
        check_that("POST request to git clone was done", git_import_req.status_code, equal_to(202))
        self.status_key = git_import_req.content
        time.sleep(5)
        git_status_response = requests.post(fixture.git_import_server + "/api/status", data=self.status_key)
        # Commenting this out as the repo is uploaded too fast and it does not show the uploading status anymore
        # check_that("git import status", git_status_response.json()["status"], contains_string("uploading"))

    @lcc.test("Verify that resources are uploaded")
    def check_resources_api(self):
        poll(lambda: requests.post(fixture.git_import_server + "/api/progress-update/resources", data=self.status_key),
             check_success=check_current_status, step=5, timeout=60)
        resources_response = requests.post(fixture.git_import_server + "/api/progress-update/resources",
                                           data=self.status_key)
        check_that("resources API status code", resources_response.status_code, equal_to(200))
        check_that("current status", resources_response.json()["current_status"], equal_to("done"))
        check_that("number of resources uploaded", resources_response.json()["total_files_uploaded"],
                   equal_to(int(number_of_resources_uploaded)))
        check_that("resources not uploaded", resources_response.json()["resources_not_uploaded"], equal_to([]))
        check_that("server message", resources_response.json()["server_message"], equal_to("Accepting requests"))
        check_that("server status", resources_response.json()["server_status"], equal_to("OK"))
        check_that("last_uploaded_file", resources_response.json()["last_uploaded_file"], is_not_none())
        check_that("modules not uploaded", resources_response.json()["resources_not_uploaded"], equal_to([]))
        resources_uploaded = resources_response.json()["resources_uploaded"]
        check_response_code(resources_uploaded, "response_code", int(number_of_resources_uploaded))
        check_not_null(resources_uploaded, "path", int(number_of_resources_uploaded))
        check_not_null(resources_uploaded, "response_details", int(number_of_resources_uploaded))

    @lcc.test("Verify that modules are uploaded")
    def check_modules_api(self):
        poll(lambda: requests.post(fixture.git_import_server + "/api/progress-update/modules", data=self.status_key),
             check_success=check_current_status, step=5, timeout=20)
        modules_response = requests.post(fixture.git_import_server + "/api/progress-update/modules",
                                         data=self.status_key)
        check_that("modules API status code", modules_response.status_code, equal_to(200))
        check_that("current status", modules_response.json()["current_status"], equal_to("done"))
        check_that("number of modules uploaded", modules_response.json()["total_files_uploaded"],
                   equal_to(int(number_of_modules_uploaded)))
        check_that("modules not uploaded", modules_response.json()["modules_not_uploaded"], equal_to([]))
        check_that("server message", modules_response.json()["server_message"], equal_to("Accepting requests"))
        check_that("server status", modules_response.json()["server_status"], equal_to("OK"))
        check_that("last_uploaded_file", modules_response.json()["last_uploaded_file"], is_not_none())
        modules_uploaded = modules_response.json()["modules_uploaded"]
        check_response_code(modules_uploaded, "response_code", int(number_of_modules_uploaded))
        check_not_null(modules_uploaded, "path", int(number_of_modules_uploaded))
        check_not_null(modules_uploaded, "response_details", int(number_of_modules_uploaded))

    @lcc.test("Verify that assemblies are uploaded")
    def check_assemblies_api(self):
        poll(lambda: requests.post(fixture.git_import_server + "/api/progress-update/assemblies", data=self.status_key),
             check_success=check_current_status, step=5, timeout=20)
        assemblies_response = requests.post(fixture.git_import_server + "/api/progress-update/assemblies",
                                            data=self.status_key)
        check_that("modules API status code", assemblies_response.status_code, equal_to(200))
        check_that("current status", assemblies_response.json()["current_status"], equal_to("done"))
        check_that("number of assemblies uploaded", assemblies_response.json()["total_files_uploaded"],
                   equal_to(int(number_of_assemblies_uploaded)))
        check_that("assemblies not uploaded", assemblies_response.json()["assemblies_not_uploaded"], equal_to([]))
        check_that("server message", assemblies_response.json()["server_message"], equal_to("Accepting requests"))
        check_that("server status", assemblies_response.json()["server_status"], equal_to("OK"))
        check_that("last_uploaded_file", assemblies_response.json()["last_uploaded_file"], is_not_none())
        assemblies_uploaded = assemblies_response.json()["assemblies_uploaded"]
        check_response_code(assemblies_uploaded, "response_code", int(number_of_assemblies_uploaded))
        check_not_null(assemblies_uploaded, "path", int(number_of_assemblies_uploaded))
        check_not_null(assemblies_uploaded, "response_details", int(number_of_assemblies_uploaded))

    @lcc.test("Verify progress-update/all API works as expected")
    def check_progress_update_all_api(self):
        response = requests.post(fixture.git_import_server + "/api/progress-update/all",
                                 data=self.status_key)
        check_that("progress-update/all API status code", response.status_code, equal_to(200))
        check_that("current status", response.json()["current_status"], equal_to("done"))
        check_that("status code for module variant created",
                   response.json()["module_variants_created"][0]["response_code"], equal_to(201))

        git_status_response = requests.post(fixture.git_import_server + "/api/status", data=self.status_key)
        check_that("git import status", git_status_response.json()["status"], contains_string("done"))

    def teardown_suite(self):
        # Deleting the git repo uploaded via git import in the test suite.
        lcc.log_info("Deleting the git repo imported...")
        path_to_git_repo = fixture.url + "bin/cpm/nodes/node.json/content/repositories/" + git_import_repo_Name
        lcc.log_info("Test repo node used for git import functionality being deleted at: %s" % path_to_git_repo)
        response_git_delete = requests.delete(path_to_git_repo, auth=(fixture.admin_username, fixture.admin_auth))
        # print(str(response_git_delete.content))
        check_that("The git import test repo was deleted successfully from backend", response_git_delete.status_code,
                   equal_to(200))


def check_current_status(response):
    current_status = response.json()["current_status"]
    print(current_status)
    return current_status == "done"


def check_response_code(response, field_name, expected_count):
    count = 0
    for res in response:
        if res[field_name] == 201 or res[field_name] == 200:
            count += 1
    check_that("count of " + field_name + " : 201 should be ", count, equal_to(expected_count))


def check_not_null(response, field_name, expected_count):
    count = 0
    for res in response:
        if res[field_name] is not None:
            count += 1
    check_that("count of " + field_name + " should not be null ", count, equal_to(expected_count))
