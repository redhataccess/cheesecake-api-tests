import lemoncheesecake.api as lcc
import git
import os
import shutil, time, datetime
import logging
import requests
import subprocess
import helpers.base as base

from lemoncheesecake.matching import *
from helpers import constants
from helpers import utilities
import json


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

test_repo_URL = base.config_reader('test_repo', 'test_repo_url')
test_repo_name = base.config_reader('test_repo', 'repo_name')
test_repo_branch = base.config_reader('test_repo', 'test_repo_branch')
git_import_repo = base.config_reader('git_import_test_repo', 'git_import_repo_name')
module_title_prefix = base.config_reader('test_repo', 'module_prefix')

# setting the appropriate URL value from env variable
env = os.environ['PANTHEON_ENV']
if env == "qa":
    url = base.config_reader('qa', 'base_url')
    git_import_server = base.config_reader('git_import_pod_details', 'qa')
    cp_url = base.config_reader('qa', 'cp_url')
    solr_url = base.config_reader('qa', 'solr_url')
elif env == "dev":
    url = base.config_reader('dev', 'base_url')
    git_import_server = base.config_reader('git_import_pod_details', 'dev')
    cp_url = base.config_reader('dev', 'cp_url')
    solr_url = base.config_reader('dev', 'solr_url')
elif env == "stage":
    url = base.config_reader('stage', 'base_url')
    git_import_server = base.config_reader('git_import_pod_details', 'stage')
    cp_url = base.config_reader('stage', 'cp_url')
    solr_url = base.config_reader('stage', 'solr_url')
elif env == "prod":
    url = base.config_reader('prod', 'base_url')
    git_import_server = base.config_reader('git_import_pod_details', 'prod')
    cp_url = base.config_reader('prod', 'cp_url')
    solr_url = base.config_reader('prod', 'solr_url')
else:
    raise Exception("Please set the env variable PANTHEON_ENV as dev/qa/stage specifically. "
                    "To run your tests against QA, run `$export PANTHEON_ENV=qa` before you run the tests")

logging.info("Tests are running against Pantheon instance: %s", url)
username = base.config_reader('login', 'username')
auth = base.config_reader('login', 'password')
uploader_username = base.config_reader('uploader', 'username')
uploader_password = base.config_reader('uploader', 'password')
admin_username = base.config_reader('admin_login', 'username')
admin_auth = base.config_reader('admin_login', 'password')

number_of_modules_uploaded = base.config_reader('test_repo', 'number_of_modules_uploaded')

# Creating product name and uri with random_string
random_string = utilities.generate_random_string(4)
# global product_name
product_name = constants.product_name + random_string
# global product_name_uri
product_name_uri = constants.product_name_uri + random_string


@lcc.fixture(scope="pre_run")
def setup_test_repo():
    logging.info("Cloning a test repo from gitlab..")
    project_dir_git = os.path.join(os.getcwd(), 'test-repo')

    if os.path.isdir(project_dir_git):
        shutil.rmtree(project_dir_git)

    os.mkdir(project_dir_git)

    repo = git.Repo.init(project_dir_git)
    origin = repo.create_remote('origin', test_repo_URL)
    origin.fetch()
    #origin.pull(origin.refs[0].remote_head)
    origin.pull(test_repo_branch)

    logging.info("Installing the Pantheon uploader script..")
    # try:
    #     subprocess.check_call(
    #         "curl -o pantheon.py https://raw.githubusercontent.com/redhataccess/pantheon/master/uploader/pantheon.py",
    #         shell=True)
    # except subprocess.CalledProcessError as e:
    #     logging.error("Unable to install the uploader script")
    #     raise e

    os.chdir(project_dir_git)

    try:
        logging.info("Using pantheon uploader to push test data to Pantheon...")

        subprocess.check_call(
            ('pantheon --user={} --password={} --server={} push'.format(uploader_username, uploader_password, url)),
            shell=True)
    except subprocess.CalledProcessError as e:
        logging.info(
            "Test setup did not complete successfully, error encountered during 'pantheon push'")
        raise e


# Creates products and add version to it using api endpoint
@lcc.fixture(scope="session")
def setup_test_products():
    lcc.log_info("Creating test product..")
    path_to_product_node = url + "content/products/" + product_name_uri
    lcc.log_info("Test Product node being created at: %s" % path_to_product_node)

    create_product_payload = {"name": product_name,
              "description": "Test product Setup description",
              "sling:resourceType": "pantheon/product",
              "jcr:primaryType": "pant:product",
              "locale": "en-US",
              "urlFragment": product_name_uri}

    # Hit the api for create product
    response = requests.post(path_to_product_node, data=create_product_payload, auth=(username, auth))
    check_that("The Product was created successfully",
               response.status_code, any_of(equal_to(201), equal_to(200)))
    lcc.log_info("Creating version for the above product")
    time.sleep(5)
    path_to_version = path_to_product_node + "/versions/{}" .format(constants.product_version)
    lcc.log_info("Product version being created for the above product: %s" % path_to_version)

    create_version_payload = {"name": constants.product_version,
                              "sling:resourceType": "pantheon/productVersion",
                              "jcr:primaryType": "pant:productVersion",
                              "urlFragment": constants.product_version_uri}


    # Hit the api for create version for the above product
    response = requests.post(path_to_version, data=create_version_payload, auth=(username, auth))
    check_that("The Product version was created successfully",
               response.status_code, any_of(equal_to(201), equal_to(200)))
    time.sleep(5)
    path_to_product_id = path_to_product_node + ".2.json"
    product_version_id_req = requests.get(path_to_product_id, auth=(username, auth))
    print(product_version_id_req.json())

    print(path_to_product_id)
    product_version_id = product_version_id_req.json()["versions"][constants.product_version]["jcr:uuid"]
    lcc.log_info("Fetching product version id of the product created: %s id: %s" % (path_to_product_id,
                                                                                    str(product_version_id)))
    return product_version_id, product_name_uri


@lcc.fixture(names=("api_auth", "auth"), scope="session")
def setup(setup_test_repo, setup_test_products):
    lcc.log_info("Initialising the session/auth...")
    session = requests.Session()
    session.auth = (username, auth)

    yield session

    # This block of code is the teardown method which deletes the repository uploaded for testing
    lcc.log_info("Deleting the test-repo from QA env...")
    path_to_repo = url + "bin/cpm/nodes/node.json/content/repositories/" + test_repo_name
    lcc.log_info("Test repo node being deleted at: %s" % path_to_repo)
    time.sleep(15)
    # body = {":operation": "delete"}
    # body = json.dumps(body)
    response = requests.delete(path_to_repo, auth=(admin_username, admin_auth))
    check_that("The test repo was deleted successfully",
               response.status_code, equal_to(200))
    time.sleep(15)
    
    # Deletes the products created using api endpoint
    lcc.log_info("Deleting test products created as a part of the tests.. ")
    path_to_new_product_node = url + "bin/cpm/nodes/node.json/content/products/" + product_name_uri
    lcc.log_info("Test Product node being deleted at: %s" % path_to_new_product_node)
    response1 = session.delete(path_to_new_product_node)
    print(str(response1.content))
    check_that("Test product version created was deleted successfully",
               response1.status_code, equal_to(200))
    time.sleep(15)




