from internet_computer.tools.inventory import CanisterFetcher


class TestCanisterFetching:
    def test_canisters_are_fetched(self):
        source_url = 'https://ic-api.internetcomputer.org/api/v3/canisters'

        limit = 2

        result_fetcher = CanisterFetcher(source_url, limit=limit).fetch()

        for _ in range(limit + 1):
            assert next(result_fetcher) is not None
