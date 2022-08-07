import json
from string import Template

import requests

from pymongo.database import Database


class Canister:
    raw_canister_url_template = Template('https://$canister_id.raw.ic0.app/')

    canister_index_template = Template('https://ic-api.internetcomputer.org/api/v3/canisters/$canister_id')

    non_web_canister_status_codes = [451, 500]

    __client: Database = None

    collection_name: str = 'canisters'

    def __init__(
        self,
        _id=None,
        canister_id=None,
        controllers=None,
        module_hash=None,
        subnet_id=None,
        last_status_code=None,
        is_web_canister=None
    ):
        self.__id = _id
        self.__canister_id = canister_id
        self.__controllers = controllers
        self.__module_hash = module_hash
        self.__subnet_id = subnet_id
        self.__last_status_code = last_status_code
        self.__is_web_canister = is_web_canister

    @property
    def _id(self):
        return self.__id

    @property
    def canister_id(self):
        return self.__canister_id

    @property
    def controllers(self):
        return self.__controllers

    @property
    def is_web_canister(self):
        return self.__is_web_canister

    @property
    def last_status_code(self):
        return self.__last_status_code

    @property
    def module_hash(self):
        return self.__module_hash

    @property
    def subnet_id(self):
        return self.__subnet_id

    @property
    def raw_canister_url(self):
        return self.raw_canister_url_template.substitute(canister_id=self.canister_id)

    def verify_web_canister(self):
        self.__last_status_code = requests.get(
            self.raw_canister_url_template.substitute(canister_id=self.canister_id)
        ).status_code

        self.__is_web_canister = self.last_status_code not in type(self).non_web_canister_status_codes

        return self.__is_web_canister

    def save(self):
        client = type(self).get_client()

        insertion_data = self.to_dict()

        insertion_data.pop('_id')
        insertion_data.pop('raw_canister_url')

        if self.__id is None:
            self.__id = client.canisters.insert_one(insertion_data).inserted_id
        else:
            client.canisters.update_one(
                {'_id': self.__id},
                {'$set': insertion_data}
            )

    def to_dict(self):
        return {
            '_id': str(self._id),
            'canister_id': self.canister_id,
            'controllers': self.controllers,
            'is_web_canister': self.__is_web_canister,
            'last_status_code': self.last_status_code,
            'module_hash': self.module_hash,
            'raw_canister_url': self.raw_canister_url,
            'subnet_id': self.subnet_id,

        }

    def to_csv(self, fields_to_output=None):
        fields = self.to_dict()

        if fields_to_output:
            return ','.join([str(fields[field]) for field in fields_to_output])

        return ','.join([
            str(self._id),
            self.canister_id,
            ' '.join(self.controllers),
            str(self.is_web_canister),
            str(self.last_status_code),
            self.module_hash,
            self.subnet_id,
        ])

    def to_json(self, fields_to_output=None):
        fields = self.to_dict()

        if fields_to_output:
            return json.dumps({field: fields[field] for field in fields_to_output})

        return json.dumps(fields)

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def csv_header(cls, fields_to_output):
        if len(fields_to_output) > 0:
            return ','.join(fields_to_output)

        return ','.join([
            '_id',
            'canister_id',
            'controllers',
            'is_web_canister',
            'last_status_code',
            'module_hash',
            'subnet_id',
        ])

    @classmethod
    def get_client(cls) -> Database:
        return cls.__client

    @classmethod
    def set_client(cls, client: Database):
        cls.__client = client

    @classmethod
    def find(cls, criteria):
        client = cls.get_client()
        found = client[cls.collection_name].find_one(criteria)
        return cls(**found)

    @classmethod
    def from_internet_computer(cls, canister_id):
        return cls(
            **requests.get(
                cls.canister_index_template.substitute(canister_id=canister_id)
            ).json()
        )

    @classmethod
    def all(cls):
        client = cls.get_client()
        finder = client[cls.collection_name].find()
        while True:
            try:
                yield cls(**finder.next())
            except StopIteration:
                break

    @classmethod
    def json_header(cls):
        return '{"data":['

    @classmethod
    def json_footer(cls):
        return ']}'


class CanisterMetadata:
    def __init__(self, source_url, offset, limit):
        self.__source_url = source_url
        self.__offset = offset
        self.__limit = limit
        self.__json_data = None
        self.__total_canisters = None
        self.__max_canister_index = None

    def __fetch_data(self):
        json_data = requests.get(
            f'{self.__source_url}?offset={self.__offset}&limit={self.__limit}'
        ).json()

        self.__total_canisters = json_data['total_canisters']
        self.__max_canister_index = json_data['max_canister_index']
        self.__json_data = json_data['data']

    @property
    def data(self):
        if self.__json_data is None:
            self.__fetch_data()

        return self.__json_data

    @property
    def max_canister_index(self):
        if self.__max_canister_index is None:
            self.__fetch_data()

        return self.__max_canister_index

    @property
    def total_canisters(self):
        if self.__total_canisters is None:
            self.__fetch_data()

        return self.__total_canisters


class CanisterFetcher:
    def __init__(self, source_url, limit=100, offset=0):
        self.__source_url = source_url
        self.__limit = limit
        self.__offset = offset

    @property
    def source_url(self):
        return self.__source_url

    @property
    def limit(self):
        return self.__limit

    @property
    def offset(self):
        return self.__offset

    @offset.setter
    def offset(self, offset):
        self.__offset = offset

    def fetch(self):
        while True:
            canister_data = CanisterMetadata(
                source_url=self.source_url,
                limit=self.limit,
                offset=self.offset
            )

            if canister_data.data is None:
                break

            for raw in canister_data.data:
                yield Canister(**raw)

            if self.offset > canister_data.max_canister_index:
                break

            self.offset += self.limit


class CanisterInventory:
    def __init__(self, fetcher):
        self.__fetcher = fetcher

    @property
    def fetcher(self):
        return self.__fetcher

    def populate(self):
        for canister in self.fetcher.fetch():
            canister.save()
