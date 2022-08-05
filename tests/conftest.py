import os
from pathlib import Path

import pytest
from pymongo.database import Database

from internet_computer.tools.pymongo_fixes import MongoClientConfigurator


@pytest.fixture(scope='session', autouse=True)
def mongo_client():
    return MongoClientHelper.mongo_client


class MongoClientHelper:
    __mongo_client: Database = None

    @classmethod
    def mongo_client(cls):
        if cls.__mongo_client is None:
            config_path = os.path.join(os.path.dirname(Path(__file__).resolve()), 'pymongo.yml')
            environment = 'test'

            cls.__mongo_client = MongoClientConfigurator(
                config_path=config_path,
                environment=environment
            ).from_config()

        return cls.__mongo_client
