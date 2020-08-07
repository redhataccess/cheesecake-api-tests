import sys
from helpers import base
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers import constants
import requests
from fixtures import fixture
from polling2 import poll
from helpers import utilities

sys.path.append("..")

module_title_prefix = base.config_reader('test_repo', 'module_prefix')


@lcc.suite("Suite: Verify that authenticated user can edit metadata and publish module", rank=1)
class test_module_edit_publish:
  api_auth = lcc.inject_fixture("api_auth")

  @lcc.test("Verify that unauthenticated user cannot edit metadata")
  def edit_metadata_no_auth(self):
    utilities.select_first_module_from_search_results(fixture.url, module_title_prefix)






