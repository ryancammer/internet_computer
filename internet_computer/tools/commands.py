import argparse
import asyncio
import os
import time
from pathlib import Path

import aiohttp

from internet_computer.tools.inventory import Canister, CanisterDataFetcher
from internet_computer.tools.pymongo_fixes import MongoClientConfigurator

#
# from multiprocessing import freeze_support, Process, Queue

DEFAULT_MAXIMUM_CANISTER_COUNT = 1000000
DEFAULT_MAXIMUM_TIME_LIMIT = 7200
DEFAULT_SOURCE_URL = 'https://ic-api.internetcomputer.org/api/v3/canisters'
DEFAULT_PYMONGO_CONFIG_PATH = 'pymongo.yml'


class CanisterWebStatusFetcher:
    DEFAULT_TASK_PROCESSOR_COUNT = 16

    command_name = 'web_status'

    def __init__(self, total_task_processors=DEFAULT_TASK_PROCESSOR_COUNT):
        self.__counter = 0
        self.__queue = asyncio.Queue()
        self.__total_task_processors = total_task_processors

    @property
    def queue(self):
        return self.__queue

    @property
    def total_task_processors(self):
        return self.__total_task_processors

    @property
    def counter(self):
        return self.__counter

    @counter.setter
    def counter(self, value):
        self.__counter = value

    async def __worker(self):
        async with aiohttp.ClientSession() as session:
            while True:
                canister = await self.queue.get()
                await canister.verify_web_canister_async(session)
                canister.save()

                self.counter -= 1

                if self.counter % 1000 == 0:
                    print(f'Processed {self.counter}. Queue size: {self.queue.qsize()}')

                self.queue.task_done()

    async def populate(self, pymongo_config_path, environment):
        mongo_client = MongoClientConfigurator(
            config_path=pymongo_config_path,
            environment=environment
        ).from_config()

        Canister.set_client(mongo_client)

        tasks = []
        for i in range(self.total_task_processors):
            task = asyncio.create_task(self.__worker())
            tasks.append(task)

        for canister in Canister.all({'last_status_code': None}):
            self.counter += 1
            if self.counter % 1000 == 0:
                print(f'Added {self.counter} canisters to process. Queue size: {self.queue.qsize()}')
            await self.queue.put(canister)

        started_at = time.monotonic()
        await self.queue.join()
        total_slept_for = time.monotonic() - started_at
        print(f'Total: {self.counter} in {total_slept_for} seconds')

        # Cancel our worker tasks.
        for task in tasks:
            task.cancel()
        # Wait until all worker tasks are cancelled.
        await asyncio.gather(*tasks, return_exceptions=True)


class CanisterFetcher:
    command_name = 'fetch_canisters'

    def __init__(self):
        pass

    def fetch(
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
        result_fetcher = CanisterDataFetcher(source_url).fetch()

        if store_to_mongo:
            config_path = pymongo_config_path
            if not Path(config_path).is_file():
                config_path = os.path.join(
                    os.path.dirname(Path(__file__).resolve()),
                    config_path
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


class MongoDumper:
    command_name = 'dump_mongo'

    def __init__(self):
        pass

    def dump(
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


class InventoryCommand:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Fetch and store canister inventory.')

        parser.add_argument(
            'command',
            default=CanisterFetcher.command_name,
            choices=[
                CanisterFetcher.command_name,
                MongoDumper.command_name,
                CanisterWebStatusFetcher.command_name
            ],
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

    async def run(self):
        args = self.args
        match args.command:
            case CanisterFetcher.command_name:
                CanisterFetcher().fetch(
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
            case MongoDumper.command_name:
                MongoDumper().dump(
                    pymongo_config_path=args.pymongo_config,
                    environment=args.environment,
                    output=args.output
                )
            case CanisterWebStatusFetcher.command_name:
                await CanisterWebStatusFetcher().populate(
                    pymongo_config_path=args.pymongo_config,
                    environment=args.environment
                )
