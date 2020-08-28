# cheesecake-api

API tests for Pantheon v2.


## Setup

### Requirements:
- Python3
- virtualenv
- virtualenvwrapper
```
$ pip install venv virtualenvwrapper
$ mkvirtualenv api-test-env
$ workon api-test-env
```
You will have virtual environment to use where you can install all your dependencies.


### Installation:
- Install all the dependencies.

``` pip3 install -r requirements.txt ```

- Set the PYTHONPATH to your current working directory

``` export PYTHONPATH=</path/to/your/tests directory> ```

```
example:
$ pwd
/home/username/sample/cheesecake-api-tests
$ export PYTHONPATH=/home/username/sample/cheesecake-api-tests

```

## Test Execution:
- Make the changes in the config file for actual values.

``` mv config.ini.sample config.ini ```
Make the appropriate changes to base URL in config.ini file.

* To run the test against QA env, set the environment variable appropriately.
``` export PANTHEON_ENV=qa ```
Acceptable values for PANTHEON_ENV variable are dev/qa/stage.

- To execute the API tests:

``` lcc run ```

- To view the report on the console:

``` lcc report ```
This command will display the last generated report on the console.

- To view the HTML report in browser:

``` firefox report/report.html ```

