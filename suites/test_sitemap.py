import requests
import lemoncheesecake.api as lcc
from helpers import base
from fixtures import fixture
from helpers import constants, utilities
from lemoncheesecake.matching import *
import xml.etree.ElementTree as ET
from datetime import datetime,timezone

@lcc.suite(description="Suite: Verify sitemap api endpoints for assembly and modules ", rank=8)
class test_sitemap:
    api_auth = lcc.inject_fixture("api_auth")
    url = fixture.url
    cp_url = fixture.cp_url
    now = datetime.now(timezone.utc)
    now_hour = int(datetime.now(timezone.utc).hour)
    now_hour_plus_one = now_hour + 1
    now_min = int(datetime.now(timezone.utc).minute)
    now_min_minus_five = now_min - 5
    now_min_plus_five = now_min + 5

    def setup_suite(self, setup_test_products):
        lcc.log_info("Setting up data for sitemap test...")
        lcc.log_info("Add metadata to and publish module::")
        assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')
        self.variant = utilities.read_variant_name_from_pantheon2config()

        self.assembly_path = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_title_prefix)
        print(self.assembly_path)
        # Add metadata to the assembly
        res, self.product_name_uri = utilities.add_metadata(fixture.url, self.assembly_path, self.variant, self.api_auth,
                                                            setup_test_products, content_type="assembly")
        # Publish the assembly
        publish_response = utilities.publish_content(fixture.url, self.assembly_path, self.variant, self.api_auth)
        # Verify if the assembly was marked released
        response = requests.get(fixture.url + self.assembly_path + "/en_US/variants/" + self.variant + ".10.json")
        check_that("Document published", response.json(), contains_string("released"))
        self.assembly_uuid = response.json()["jcr:uuid"]
        print(self.assembly_uuid)

        module_title_prefix = base.config_reader('test_repo', 'module_prefix')
        self.module_path = utilities.select_nth_item_from_search_results(0, fixture.url, module_title_prefix)
        print(self.module_path)
        # Add metadat to module
        module_res, self.product_name_uri = utilities.add_metadata(fixture.url, self.module_path, self.variant, self.api_auth,
                                                            setup_test_products, content_type="module")
        # Publish the module
        m_publish_response = utilities.publish_content(fixture.url, self.module_path, self.variant, self.api_auth)
        # Verify if the module was marked released
        module_response = requests.get(fixture.url + self.module_path + "/en_US/variants/" + self.variant + ".10.json")
        check_that("Document published", module_response.json(), contains_string("released"))
        self.module_uuid = module_response.json()["jcr:uuid"]
        print(self.module_uuid)

    @lcc.test("Verify api endpoint for assembly sitemap returns expected data")
    def verify_assembly_sitemap(self, api_auth):
        lcc.log_info("Verifying sitemap for assemblies")
        req = self.url + "api/sitemap/assembly.sitemap.xml"
        response = requests.get(req)
        url_loc = self.cp_url + "documentation/en-us/" + self.product_name_uri + "/" + constants.product_version_uri + "/guide/" + self.assembly_uuid
        # Verify that assembly sitemap response contains recently published assembly url
        check_that("Assembly Sitemap response", response.text, contains_string(url_loc))
        xmlDict = {}
        root = ET.fromstring(response.content)
        for child in root.iter('*'):
            print(child.tag)
        for sitemap in root:
            children = sitemap.getchildren()
            xmlDict[children[0].text] = children[1].text
        # Extract published date for recent assembly from the sitemap
        publish_date = xmlDict[url_loc]
        print(publish_date)
        date = publish_date.split("T")

        # Verify that published date is same as current date
        check_that("Published date",date[0], equal_to(str(self.now.date())))
        temp = date[1].split(".")
        time = temp[0]
        t=time.split(":")
        hour = t[0]
        min = t[1]
        sec = t[2]

        # Verify that assembly publish time is withing current time range
        all_of(check_that("Published time (Hour)", int(hour), is_between(self.now_hour, self.now_hour_plus_one)),
        check_that("Published time (Min)", int(min), is_between(self.now_min_minus_five, self.now_min_plus_five)))
        
        # Unpublishing the assembly
        res = utilities.unpublish_content(fixture.url, self.assembly_path, self.variant, self.api_auth)
        draft = requests.get(fixture.url + self.assembly_path + "/en_US/variants/" + self.variant + ".10.json")
        # Check that assembly is unpublished successfully
        assert_that("Document unpublished", draft.json(), contains_string("draft"))
        response1 = requests.get(req)
        # Verify unpublished module not listed in sitemap
        check_that("Assembly Sitemap response", response1.text, not_(contains_string(url_loc)))


    @lcc.test("Verify api endpoint for module sitemap returns expected data")
    def verify_module_sitemap(self, api_auth):
        lcc.log_info("Verifying sitemap for module")
        req = self.url + "api/sitemap/module.sitemap.xml"
        response = requests.get(req)
        url_loc = self.cp_url + "documentation/en-us/" + self.product_name_uri + "/" + constants.product_version_uri + "/topic/" + self.module_uuid
        check_that("Module Sitemap response", response.text, contains_string(url_loc))
        xmlDict = {}
        root = ET.fromstring(response.content)
        for child in root.iter('*'):
            print(child.tag)
        for sitemap in root:
            children = sitemap.getchildren()
            xmlDict[children[0].text] = children[1].text
        publish_date = xmlDict[url_loc]
        print(publish_date)
        date = publish_date.split("T")
        # Verify that published date is same as current date
        check_that("Published date", date[0], equal_to(str(self.now.date())))
        temp = date[1].split(".")
        time = temp[0]
        t = time.split(":")
        hour = t[0]
        min = t[1]
        sec = t[2]
        # Verify that module publish time is withing current time range
        all_of(check_that("Published time (Hour)", int(hour), is_between(self.now_hour, self.now_hour_plus_one)),
               check_that("Published time (Min)", int(min),
                          is_between(self.now_min_minus_five, self.now_min_plus_five)))
        # Unpublishing the module
        res = utilities.unpublish_content(fixture.url, self.module_path, self.variant, self.api_auth)
        draft = requests.get(fixture.url + self.module_path + "/en_US/variants/" + self.variant + ".10.json")
        # Check that the modules was unpublished successfully
        assert_that("Document unpublished", draft.json(), contains_string("draft"))
        response1 = requests.get(req)
        # Verify unpublished module not listed in sitemap
        check_that("Module Sitemap response", response1.text, not_(contains_string(url_loc)))