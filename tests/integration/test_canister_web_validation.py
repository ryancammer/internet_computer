import requests

from internet_computer.tools.inventory import Canister, CanisterFetcher
from tests.conftest import MongoClientHelper


class TestCanisterWebValidation:
    @classmethod
    def setup_class(cls):
        Canister.set_client(MongoClientHelper.mongo_client())
        MongoClientHelper.mongo_client().drop_collection(Canister.collection_name)

    @classmethod
    def teardown_class(cls):
        MongoClientHelper.mongo_client().drop_collection(Canister.collection_name)

    def test_canister_web_validation_is_false_for_non_web_canister(self):
        fetcher = CanisterFetcher(
            source_url='https://ic-api.internetcomputer.org/api/v3/canisters',
            limit=100
        ).fetch()

        canister_id = None

        for canister in fetcher:
            if requests.get(canister.raw_canister_url).status_code == 500:
                canister_id = canister.canister_id
                break

        print(canister_id)

        canister = Canister.from_internet_computer(canister_id)
        canister.verify_web_canister()
        print(canister.raw_canister_url)
        assert canister.is_web_canister is False

    def test_canister_web_validation_is_true_for_web_canister(self):
        fetcher = CanisterFetcher(
            source_url='https://ic-api.internetcomputer.org/api/v3/canisters',
            limit=100
        ).fetch()

        canister_id = None

        for canister in fetcher:
            if requests.get(canister.raw_canister_url).status_code == 200:
                canister_id = canister.canister_id
                break

        print(canister_id)

        canister = Canister.from_internet_computer(canister_id)
        canister.verify_web_canister()
        print(canister.raw_canister_url)
        assert canister.is_web_canister is True
