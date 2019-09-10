import lemoncheesecake.api as lcc
import json
import os


@lcc.fixture()
def module_details():
    json_file = json.load(open(os.path.join(os.getcwd(), 'fixtures', 'module.json')))
    module_id = json_file["module_id"]
    print(module_id)
    return module_id


