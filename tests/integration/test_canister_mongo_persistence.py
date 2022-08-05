from internet_computer.tools.inventory import Canister
from tests.conftest import MongoClientHelper


class TestCanisterMongoPersistence:
    @classmethod
    def setup_class(cls):
        Canister.set_client(MongoClientHelper.mongo_client())
        MongoClientHelper.mongo_client().drop_collection(Canister.collection_name)

    @classmethod
    def teardown_class(cls):
        MongoClientHelper.mongo_client().drop_collection(Canister.collection_name)

    def test_a_canister_is_persisted_and_retrieved(self, mongo_client):
        canister = Canister(
            canister_id='2226x-viaaa-aaaaj-aab3q-cai',
            controllers=[
                'ujkeo-2rcd5-pew4p-pkvrt-gpxo3-gmr7j-rssd3-jgk44-aq6dg-snvsw-mqe'
            ],
            module_hash='1404b28b1c66491689b59e184a9de3c2be0dbdd75d952f29113b516742b7f898',
            subnet_id='qdvhd-os4o2-zzrdw-xrcv4-gljou-eztdp-bj326-e6jgr-tkhuc-ql6v2-yqe'
        )

        canister.save()

        found_canister = Canister.find({'canister_id': canister.canister_id})

        assert canister.canister_id == found_canister.canister_id
        assert canister.controllers == found_canister.controllers
        assert canister.module_hash == found_canister.module_hash
        assert canister.subnet_id == found_canister.subnet_id
        assert canister.controllers == found_canister.controllers
        assert canister._id == found_canister._id
