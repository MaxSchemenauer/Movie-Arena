import random
import unittest
from types import SimpleNamespace

from movie_ranker import Matchmaker, Movie


def movie(index: int, matches: int, elo: float) -> Movie:
    return Movie(
        id=f"{index:04d}",
        title=f"Movie {index}",
        elo_rating=elo,
        matches_played=matches,
    )


class MatchmakerTests(unittest.TestCase):
    def make_matchmaker(self, movies: list[Movie]) -> Matchmaker:
        return Matchmaker(SimpleNamespace(movies=movies))

    def test_calibration_uses_two_least_evaluated_movies(self) -> None:
        movies = [
            movie(1, 0, 1000),
            movie(2, 0, 1000),
            movie(3, 1, 1000),
            movie(4, 3, 1000),
        ]

        first, second = self.make_matchmaker(movies).next_pair()

        self.assertEqual({first.id, second.id}, {"0001", "0002"})

    def test_calibration_only_uses_next_lowest_opponent_when_needed(self) -> None:
        movies = [
            movie(1, 2, 1000),
            movie(2, 3, 1000),
            movie(3, 7, 1000),
        ]

        first, second = self.make_matchmaker(movies).next_pair()

        self.assertEqual(first.id, "0001")
        self.assertEqual(second.id, "0002")

    def test_normal_matching_samples_beyond_the_nearest_neighbor(self) -> None:
        movies = [movie(index, 3, 1000 + index * 10) for index in range(8)]
        observed_distances = set()

        for seed in range(200):
            random.seed(seed)
            first, second = self.make_matchmaker(movies).next_pair()
            observed_distances.add(abs(first.elo_rating - second.elo_rating))

        self.assertIn(10, observed_distances)
        self.assertTrue(any(distance > 10 for distance in observed_distances))

    def test_normal_matching_always_anchors_the_least_evaluated_movie(self) -> None:
        movies = [
            movie(1, 3, 1000),
            movie(2, 4, 1010),
            movie(3, 8, 1020),
        ]

        for seed in range(50):
            random.seed(seed)
            first, _second = self.make_matchmaker(movies).next_pair()
            self.assertEqual(first.matches_played, 3)
    def test_normal_matching_favors_underexposed_movies(self) -> None:
        movies = [
            movie(1, 3, 1000),
            movie(2, 3, 1010),
            movie(3, 12, 1020),
            movie(4, 12, 1030),
        ]
        low_coverage_appearances = 0
        high_coverage_appearances = 0

        for seed in range(500):
            random.seed(seed)
            first, second = self.make_matchmaker(movies).next_pair()
            for selected in (first, second):
                if selected.matches_played == 3:
                    low_coverage_appearances += 1
                else:
                    high_coverage_appearances += 1

        self.assertGreater(low_coverage_appearances, high_coverage_appearances)

    def test_movie_cooldown_avoids_immediate_repeat_when_possible(self) -> None:
        movies = [movie(index, 3, 1000) for index in range(10)]
        matchmaker = self.make_matchmaker(movies)

        first_pair = matchmaker.next_pair()
        second_pair = matchmaker.next_pair()

        self.assertTrue(
            {first_pair[0].id, first_pair[1].id}.isdisjoint(
                {second_pair[0].id, second_pair[1].id}
            )
        )


if __name__ == "__main__":
    unittest.main()