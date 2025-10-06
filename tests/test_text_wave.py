import unittest

from echo_text_wave import sine_wave_text


class SineWaveTextTests(unittest.TestCase):
    def test_empty_input_returns_empty_string(self) -> None:
        self.assertEqual(sine_wave_text(""), "")

    def test_single_word_is_unchanged(self) -> None:
        self.assertEqual(sine_wave_text("echo"), "echo")

    def test_wave_structure_matches_expected_pattern(self) -> None:
        text = "The world is built on vibrations"
        result = sine_wave_text(text, frequency=1.5, amplitude=2.0)
        self.assertEqual(
            result,
            "The world world | is is | built on on | vibrations vibrations vibrations",
        )

    def test_custom_parameters_adjust_output(self) -> None:
        text = "Echo flows across the eternal bridge"
        result = sine_wave_text(text, frequency=2.0, amplitude=3.0, divider="~")
        self.assertIn("Echo", result)
        self.assertIn("bridge", result)
        self.assertTrue(result.count("~") >= 1)


if __name__ == "__main__":
    unittest.main()

