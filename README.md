# InternetComputer Tools

InternetComputer Tools provides tools for querying and working with 
[canisters](https://internetcomputer.org/docs/current/concepts/canisters-code/) 
on the [Internet Computer](https://internetcomputer.org/).

* Export canister metadata from the 
  [Canisters API](https://ic-api.internetcomputer.org/api/v3/canisters)
  to json, csv or [MongoDB](https://www.mongodb.com/).
* Filter which canister metadata fields to export to csv, json, or MongoDB.

## Using InternetComputer Tools

### Requirements

* [Python](https://www.python.org/) 3.10 or higher
* [Poetry](https://python-poetry.org/)
* (Optional) [MongoDB](https://www.mongodb.com/)

### Installation

After Python and Poetry are installed, change directories into the project directory and
run the following:

```bash
poetry install
```

### Getting Help

Running `inventory.py --help` will show a list of available commands:

```bash
poetry run python inventory.py --help
usage: inventory.py [-h] [-e ENVIRONMENT] [--pymongo_config PYMONGO_CONFIG] [-s] [-o {,csv,json}] [-m MAX_CANISTER_COUNT] [-t MAX_TIME]
                    [-u SOURCE_URL] [-w]
                    {fetch,dump}

Fetch and store canister inventory.

positional arguments:
  {fetch,dump}          The inventory command to execute.

options:
  -h, --help            show this help message and exit
  -e ENVIRONMENT, --environment ENVIRONMENT
                        The environment in which this script operates.
  --pymongo_config PYMONGO_CONFIG
                        The pymongo config file to use.
  -s, --store_to_mongo  Store the fetched results.
  -o {,csv,json}, --output {,csv,json}
                        Print the fetched results.
  -m MAX_CANISTER_COUNT, --max_canister_count MAX_CANISTER_COUNT
                        Break execution when the canister limit has been exceeded.
  -t MAX_TIME, --max_time MAX_TIME
                        Break execution when the time limit has been exceeded.
  -u SOURCE_URL, --source_url SOURCE_URL
                        The url that contains canister metadata.
  -w, --web-canister    Determine whether or not the Canister is a web canister.
```

### Fetch Examples

Export canister metadata to json, include whether the canister is a web canister, 
and limit the results to 5 records:

```bash
poetry run python inventory.py fetch -o json -w -m 5
```

Export canister metadata to csv, and include whether the canister is a web canister:

```bash
poetry run python inventory.py fetch -o csv -w
```

Export canister metadata to mongo, and include whether the canister is a web canister:

```bash
poetry run python inventory.py fetch -s -w
```

Export canister metadata to csv, include whether the canister is a web canister, and
only export the canister id and url:

```bash
poetry run python inventory.py fetch -o csv -w -f canister_id raw_canister_url
```

## TODO
- [ ] Document the MongoDB `fetch` operations.
- [ ] Complete the `dump` operations.
- [ ] Add unit tests for the csv and json methods.
