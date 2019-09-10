import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
import requests
from helpers import base


SUITE = {
    "description": "Tests for GET /api/module?module_id=<module_id>"
}

url = base.base_url()


@lcc.test("Verify that GET request for /api/module?locale=en-us&module_id=<module_id> gives a 200 OK")
def test_get_module(module_details):
    lcc.set_step("checking for endpoint: /api/module?locale=en-us&module_id=" + module_details)
    response = requests.get(url=url + "/api/module?locale=en-us&module_id=" + module_details)
    check_that("response code", response.status_code, equal_to(200), quiet=False)


@lcc.test("Verify that GET request for /api/module?locale=en-us&module_id=<module_id> contains all the required params")
def test_get_module_response(module_details):
    response = requests.get(url=url + "/api/module?locale=en-us&module_id=" + module_details)
    result = response.json()
    check_that("the response ", result, has_entry("module"))
    check_that("the response ", result, has_entry("status"))
    check_that("the response ", result, has_entry("message"))

@lcc.test("Verify that GET request for /api/module has the required params for module JSON oject")
def test_get_module_details(module_details):
    response = requests.get(url=url + "/api/module?locale=en-us&module_id=" + module_details)
    result = response.json()["module"]
    check_that("the response  object 'module'", result, has_entry("module_uuid"))
    check_that("the response  object 'module'", result, has_entry("locale"))
    check_that("the response  object 'module'", result, has_entry("title"))
    check_that("the response  object 'module' ", result, has_entry("description"))
    check_that("the response  object 'module'", result, has_entry("body"))
    check_that("the response  object 'module'", result, has_entry("product_name"))
    check_that("the response  object 'module'", result, has_entry("product_version"))
    check_that("the response  object 'module'", result, has_entry("content_type"))
    check_that("the response  object 'module'", result, has_entry("date_modified"))
    check_that("the response  object 'module'", result, has_entry("date_published"))
    check_that("the response  object 'module'", result, has_entry("context_id"))
    check_that("the response  object 'module'", result, has_entry("headline"))
    check_that("the response  object 'module'", result, has_entry("module_url_fragment"))
    check_that("the response  object 'module'", result, has_entry("revision_id"))
    check_that("the response  object 'module'", result, has_entry("context_url_fragment"))

