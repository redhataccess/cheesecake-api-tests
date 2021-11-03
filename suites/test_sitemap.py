import requests
import lemoncheesecake.api as lcc
from helpers import base
from fixtures import fixture
from helpers import constants, utilities
from lemoncheesecake.matching import *
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import xmltodict
import json

proxy_server = base.config_reader('proxy', 'proxy_server')

proxies = {
    "http": proxy_server,
    "https": proxy_server,
}
header={'User-Agent': 'Chrome'}

@lcc.suite(description="Suite: Verify sitemap api endpoints for assembly and modules", rank=8)
class test_sitemap:
    api_auth = lcc.inject_fixture("api_auth")
    now = datetime.now(timezone.utc)
    # now_hour = int(datetime.now(timezone.utc).hour)
    # now_hour_plus_one = now_hour + 1
    # now_min = int(datetime.now(timezone.utc).minute)
    # now_min_minus_ten = now_min - 15
    # now_min_plus_ten = now_min + 15
    # if(now_min_plus_ten >= 60):
    #     now_min_plus_ten = now_min_plus_ten-60
    # if(now_min_minus_ten < 0):
    #     now_min_minus_ten = 0
    #
    # def check_time_range(time_read):
    range = now + timedelta(minutes=15)

    def setup_suite(self, setup_test_products, api_auth):
        lcc.log_info("Setup: Adding metadata and publishing module, assembly to test the sitemap endpoint...")
        lcc.log_info("Adding metadata, publishing the assembly first...")
        assembly_title_prefix = base.config_reader('test_repo', 'assembly_prefix')
        self.variant = utilities.read_variant_name_from_pantheon2config()

        self.assembly_path = utilities.select_nth_item_from_search_results(1, fixture.url, assembly_title_prefix,
                                                                           api_auth)
        lcc.log_info("Assembly path for tests: %s" % self.assembly_path)
        # Add metadata to the assembly
        res, self.product_name_uri = utilities.add_metadata(fixture.url, self.assembly_path, self.variant,
                                                            self.api_auth,
                                                            setup_test_products, content_type="assembly")
        # Publish the assembly
        publish_response = utilities.publish_content(fixture.url, self.assembly_path, self.variant, self.api_auth)
        check_that("Publish Assembly response status ", publish_response.status_code, equal_to(200))

        # Verify if the assembly was marked released
        response = api_auth.get(fixture.url + self.assembly_path + "/en_US/variants/" + self.variant + ".10.json")
        check_that("Assembly was published", response.json(), has_entry("released"))
        self.assembly_uuid = response.json()["jcr:uuid"]
        lcc.log_info("Assembly published uuid: %s" % self.assembly_uuid)

        lcc.log_info("Publishing a module now...")
        module_title_prefix = base.config_reader('test_repo', 'module_prefix')
        self.module_path = utilities.select_nth_item_from_search_results(0, fixture.url, module_title_prefix, api_auth)
        print(self.module_path)
        # Add metadat to module
        module_res, self.product_name_uri = utilities.add_metadata(fixture.url, self.module_path, self.variant,
                                                                   self.api_auth,
                                                                   setup_test_products, content_type="module")
        # Publish the module
        m_publish_response = utilities.publish_content(fixture.url, self.module_path, self.variant, self.api_auth)
        # Verify if the module was marked released
        module_response = api_auth.get(fixture.url + self.module_path + "/en_US/variants/" + self.variant + ".10.json")
        check_that("Document published", module_response.json(), has_entry("released"))
        self.module_uuid = module_response.json()["jcr:uuid"]
        lcc.log_info("Module published uuid: %s " % self.module_uuid)

    @lcc.test("Verify api endpoint for assembly sitemap: api/sitemap/assembly.sitemap.xml contains published assembly")
    def verify_assembly_sitemap(self, api_auth):
        lcc.log_info("Verifying sitemap for assemblies")
        req = fixture.url + "api/sitemap/assembly.sitemap.xml"
        response = api_auth.get(req)
        url_loc = fixture.cp_url + "documentation/en-us/" + self.product_name_uri + "/" + constants.product_version_uri + "/guide/" + self.assembly_uuid
        # Verify that assembly sitemap response contains recently published assembly url
        check_that("Assembly Sitemap response at endpoint: %s" % req, response.text, contains_string(url_loc))

        xml_dict = {}
        xml_dict_ord = xmltodict.parse(response.text)
        xml_dict = json.loads(json.dumps(xml_dict_ord))
        lcc.log_info("Creating a dict for the sitemap endpoint responses for verification...")

        print(xml_dict.items())
        #lcc.log_(xml_dict.items())

        # Extract published date for recent assembly from the sitemap
        publish_date = ""
        for k1, v1 in xml_dict.items():
            for k2, v2 in v1.items():
                if (k2 == "url"):
                    for i in range(len(xml_dict[k1][k2])):
                        if xml_dict[k1][k2][i]['loc'] == url_loc:
                            publish_date = xml_dict[k1][k2][i]['lastmod']
                            break

        check_that("publish_date value assignment check ", publish_date, not_equal_to(""))
        #publish_date = xml_dict[url_loc]
        lcc.log_info("Extracting the publish date for %s as %s" % (url_loc, publish_date))
        # date = publish_date.split("T")
        #
        # # Verify that published date is same as current date
        # check_that("Published date", date[0], equal_to(str(self.now.date())))
        #
        # t = date[1].split(".")[0].split(":")
        # hour = t[0]
        # min = t[1]
        # sec = t[2]
        # lcc.log_info("Time now: %s" % str(self.now.time()))
        # lcc.log_info("Published time to match: %s " % str(t))
        publish_date = publish_date.replace("Z", "+00:00")
        published_date = datetime.fromisoformat(publish_date)
        flag = False
        if (self.now <= published_date <= self.range):
            flag = True

        check_that("Published date and time is in range %s to %s" % (self.now, self.range), flag, is_true())

        # # Verify that assembly publish time is within current time range
        # all_of(check_that("Published time (Hour)", int(hour), is_between(self.now_hour, self.now_hour_plus_one)),
        #        check_that("Published time (Min)", int(min), is_between(self.now_min_minus_ten, self.now_min_plus_ten)))

        lcc.log_info("Verifying if unpublishing the assembly removes it from the sitemap...")
        # Unpublishing the assembly
        res = utilities.unpublish_content(fixture.url, self.assembly_path, self.variant, self.api_auth)
        draft = api_auth.get(fixture.url + self.assembly_path + "/en_US/variants/" + self.variant + ".10.json")
        # Check that assembly is unpublished successfully
        assert_that("Document unpublished", draft.json(), has_entry("draft"))
        response1 = api_auth.get(req)
        # Verify unpublished module not listed in sitemap
        check_that("Assembly Sitemap response", response1.text, not_(contains_string(url_loc)))

    @lcc.test("Verify api endpoint for module sitemap: api/sitemap/module.sitemap.xml contains published module")
    def verify_module_sitemap(self, api_auth):
        lcc.log_info("Verifying sitemap for module")
        req = fixture.url + "api/sitemap/module.sitemap.xml"
        response = api_auth.get(req)
        url_loc = fixture.cp_url + "documentation/en-us/" + self.product_name_uri + "/" + constants.product_version_uri + "/topic/" + self.module_uuid
        check_that("Module Sitemap response at endpoint: %s" % req, response.text, contains_string(url_loc))

        xml_dict = {}

        print(url_loc)
        print(type(response.text))
        xml_dict_ord = xmltodict.parse(response.text)
        xml_dict = json.loads(json.dumps(xml_dict_ord))
        lcc.log_info("Creating a dict for the sitemap endpoint responses for verification...")
        # lcc.log_info(root)

        # Extract published date for recent assembly from the sitemap

        publish_date = ""
        for k1, v1 in xml_dict.items():
            for k2, v2 in v1.items():
                if (k2 == "url"):
                    for i in range(len(xml_dict[k1][k2])):
                        if xml_dict[k1][k2][i]['loc'] == url_loc:
                            publish_date = xml_dict[k1][k2][i]['lastmod']
                            break

        check_that("publish_date value assignment check ", publish_date, not_equal_to(""))
        lcc.log_info("Extracting the publish date for %s as %s" % (url_loc, publish_date))
        # date = publish_date.split("T")
        #
        # # Verify that published date is same as current date
        # check_that("Published date", date[0], equal_to(str(self.now.date())))
        #
        # t = date[1].split(".")[0].split(":")
        # hour = t[0]
        # min = t[1]
        # sec = t[2]
        # lcc.log_info("Time now: %s" % str(self.now.time()))
        # lcc.log_info("Published time to match: %s " % str(t))
        # # Verify that module publish time is withing current time range
        # all_of(check_that("Published time (Hour)", int(hour), is_between(self.now_hour, self.now_hour_plus_one)),
        #        check_that("Published time (Min)", int(min),
        #                   is_between(self.now_min_minus_ten, self.now_min_plus_ten)))
        publish_date = publish_date.replace("Z", "+00:00")
        published_date = datetime.fromisoformat(publish_date)
        flag = False
        if (self.now <= published_date <= self.range):
            flag = True

        check_that("Published date and time is in range %s to %s" % (self.now, self.range), flag, is_true())

        lcc.log_info("Verifying if unpublishing a module removes it from the sitemap.xml... ")

        # Unpublishing the module
        res = utilities.unpublish_content(fixture.url, self.module_path, self.variant, self.api_auth)
        draft = api_auth.get(fixture.url + self.module_path + "/en_US/variants/" + self.variant + ".10.json")
        # Check that the modules was unpublished successfully
        assert_that("Document unpublished", draft.json(), has_entry("draft"))
        response1 = api_auth.get(req)
        # Verify unpublished module not listed in sitemap
        check_that("Module Sitemap response", response1.text, not_(contains_string(url_loc)))

    @lcc.test("Verify sitemap API endpoint behind akamai")
    def verify_module_sitemap_behind_akamai(self, api_auth):
        req1 = fixture.behind_akamai_url + "api/sitemap/module.sitemap.xml"
        lcc.log_info(req1)
        response1 = api_auth.get(req1, proxies=proxies, headers=header)
        check_that("status code for Module Sitemap API behind akamai", response1.status_code, equal_to(200))

        req2 = fixture.behind_akamai_url + "api/sitemap/assembly.sitemap.xml"
        lcc.log_info(req2)
        response2 = api_auth.get(req2, proxies=proxies, headers=header)
        check_that("status code for Assembly Sitemap API behind akamai", response2.status_code, equal_to(200))

    @lcc.test("Verify sitemap API endpoint external proxy")
    def verify_module_sitemap_ext_proxy(self, api_auth):
        req1 = fixture.external_proxy_url + "sitemap/module.sitemap.xml"
        lcc.log_info(req1)
        response1 = api_auth.get(req1, proxies=proxies, headers=header)
        check_that("status code for Module Sitemap API for external proxy", response1.status_code, equal_to(200))

        req2 = fixture.external_proxy_url + "sitemap/assembly.sitemap.xml"
        lcc.log_info(req2)
        response2 = api_auth.get(req2, proxies=proxies, headers=header)
        check_that("status code for Assembly Sitemap API for external proxy", response2.status_code, equal_to(200))
