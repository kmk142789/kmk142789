import unittest

from atlas.search import filter_entries, parse_structured


SAMPLE = [
    {"cycle": 1, "puzzle_id": 130, "address": "1AAA", "title": "A", "digest": "d1", "source": "x"},
    {"cycle": 2, "puzzle_id": 130, "address": "1AAA", "title": "A2", "digest": "d2", "source": "y"},
    {"cycle": 2, "puzzle_id": 131, "address": "1BBB", "title": "B", "digest": "d3", "source": "z"},
]


class TestAtlasSearchHelpers(unittest.TestCase):
    def test_parse(self) -> None:
        query = parse_structured("cycle:2 puzzle:130 addr:1aAa")
        self.assertEqual(query["cycle"], 2)
        self.assertEqual(query["puzzle_id"], 130)
        self.assertEqual(query["address"], "1aAa")

    def test_filter_cycle(self) -> None:
        results = filter_entries(SAMPLE, cycle=2)
        self.assertEqual(len(results), 2)

    def test_filter_combo(self) -> None:
        results = filter_entries(SAMPLE, cycle=2, puzzle_id=130, address="1aaa")
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
