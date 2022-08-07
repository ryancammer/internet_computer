import argparse
import os
import time
from pathlib import Path

from internet_computer.tools.inventory import CanisterFetcher, Canister
from internet_computer.tools.pymongo_fixes import MongoClientConfigurator

DEFAULT_MAXIMUM_CANISTER_COUNT = 1000000
DEFAULT_MAXIMUM_TIME_LIMIT = 7200
DEFAULT_SOURCE_URL = 'https://ic-api.internetcomputer.org/api/v3/canisters'
DEFAULT_PYMONGO_CONFIG_PATH = 'pymongo.yml'


class InventoryCommand:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Fetch and store canister inventory.')

        parser.add_argument(
            'command',
            default='fetch',
            choices=['fetch', 'dump'],
            type=str,
            help='The inventory command to execute.')

        parser.add_argument(
            '-e',
            '--environment',
            default='development',
            type=str,
            help='The environment in which this script operates.')

        parser.add_argument(
            '-f',
            '--fields_to_output',
            default=None,
            type=str,
            nargs='+',
            help='The fields to export.')

        parser.add_argument(
            '-m',
            '--max_canister_count',
            type=int,
            default=DEFAULT_MAXIMUM_CANISTER_COUNT,
            help='Break execution when the canister limit has been exceeded.')

        parser.add_argument(
            '-o',
            '--output',
            default='',
            choices=['', 'csv', 'json'],
            help='Print the fetched results.')

        parser.add_argument(
            '-p',
            '--pymongo_config',
            type=str,
            default=DEFAULT_PYMONGO_CONFIG_PATH,
            help='The pymongo config file to use.')

        parser.add_argument(
            '-s',
            '--store_to_mongo',
            action='store_true',
            help='Store the fetched results.')

        parser.add_argument(
            '-t',
            '--max_time',
            type=int,
            default=DEFAULT_MAXIMUM_TIME_LIMIT,
            help='Break execution when the time limit has been exceeded.')

        parser.add_argument(
            '-u',
            '--source_url',
            type=str,
            default=DEFAULT_SOURCE_URL,
            help='The url that contains canister metadata.')

        parser.add_argument(
            '-w',
            '--web-canister',
            action='store_true',
            help='Determine whether or not the Canister is a web canister.'
        )

        self.parser = parser

        self.args = self.parser.parse_args()

    def run(self):
        args = self.args
        match args.command:
            case 'fetch':
                self.__fetch(
                    source_url=args.source_url,
                    pymongo_config_path=args.pymongo_config,
                    environment=args.environment,
                    fields_to_output=args.fields_to_output,
                    store_to_mongo=args.store_to_mongo,
                    output=args.output,
                    maximum_canister_count=args.max_canister_count,
                    maximum_time_limit=args.max_time,
                    verify_web_canister=args.web_canister
                )
            case 'dump':
                self.__dump(
                    pymongo_config_path=args.pymongo_config,
                    environment=args.environment,
                    output=args.output
                )

    def __dump(
        self,
        pymongo_config_path,
        environment,
        output
    ):
        mongo_client = MongoClientConfigurator(
            config_path=pymongo_config_path,
            environment=environment
        ).from_config()

        Canister.set_client(mongo_client)

        for canister in Canister.all():
            match output:
                case 'csv':
                    print(canister.to_csv())
                case 'json':
                    print(canister.to_json())
                case '':
                    pass

    def __fetch(
        self,
        pymongo_config_path,
        environment,
        fields_to_output,
        maximum_canister_count,
        maximum_time_limit,
        output,
        source_url,
        store_to_mongo,
        verify_web_canister
    ):
        result_fetcher = CanisterFetcher(source_url).fetch()

        if store_to_mongo:
            config_path = os.path.join(
                os.path.dirname(Path(__file__).resolve()),
                pymongo_config_path
            )

            mongo_client = MongoClientConfigurator(
                config_path=config_path,
                environment=environment
            ).from_config()

            Canister.set_client(mongo_client)

        start_time = time.time()

        canister_count = 0

        output_comma = False

        match output:
            case 'csv':
                print(Canister.csv_header(fields_to_output))
            case 'json':
                print(Canister.json_header())
            case '':
                pass

        for canister in result_fetcher:
            canister_count += 1

            if canister is None or canister_count > maximum_canister_count:
                break

            if output_comma:
                print(',')

            if verify_web_canister:
                canister.verify_web_canister()

            if store_to_mongo:
                canister.save()

            match output:
                case 'csv':
                    print(canister.to_csv(fields_to_output))
                case 'json':
                    print(canister.to_json(fields_to_output), end='')
                    output_comma = True
                case '':
                    pass

            if time.time() - start_time >= maximum_time_limit:
                break

        match output:
            case 'csv':
                print('')
            case 'json':
                print(Canister.json_footer())
            case '':
                pass
