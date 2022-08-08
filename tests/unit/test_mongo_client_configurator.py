import os
from pathlib import Path
import yaml

from ic0_fraud_detection.pymongo_fixes import MongoClientConfigurator


def test_it_returns_an_error_when_there_is_no_config_file():
    try:
        MongoClientConfigurator(config_path='', environment='development').from_config()
    except FileNotFoundError as error:
        assert error.strerror == 'No such file or directory'


def test_it_returns_a_mongo_client_with_proper_environment():
    config_path = os.path.join(os.path.dirname(Path(__file__).resolve()), 'pymongo.yml')
    environment = 'development'

    mongo_client = MongoClientConfigurator(
        config_path=config_path,
        environment=environment
    ).from_config()

    assert 'my_db' == mongo_client.name
