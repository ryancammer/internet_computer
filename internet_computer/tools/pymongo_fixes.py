import pymongo
import yaml
from pymongo.database import Database


class MongoClientConfigurator:
    DEFAULT_ENVIRONMENT = 'development'

    def __init__(self, config_path, environment=DEFAULT_ENVIRONMENT):
        self.__config_path = config_path
        self.__environment = environment

    @property
    def config_path(self):
        return self.__config_path

    @property
    def environment(self):
        return self.__environment

    def from_config(self) -> Database:
        with open(self.config_path, 'r') as stream:
            try:
                parsed_yaml = yaml.safe_load(stream)
                environment_config = parsed_yaml[self.environment]
                default_client = environment_config['clients']['default']
                mongo_client = pymongo.MongoClient(
                    host=default_client['hosts']
                )

                return mongo_client[default_client['database']]

            except yaml.YAMLError as error:
                # TODO: check for logger and log error
                raise
