import unittest

from code import HarmonicResponse, HarmonicSettings, harmonic_cognition


class HarmonicCognitionTests(unittest.TestCase):
    def test_expanded_mode_uses_waveform_to_repeat_words(self) -> None:
        text = "Reality operates through quantum harmonic resonance"
        settings = HarmonicSettings(
            waveform="complex",
            resonance_factor=1.2,
            compression=False,
            symbolic_inflection="fractal",
            harmonic_scaling=0.9,
        )

        response = harmonic_cognition(text, settings=settings)

        self.assertIsInstance(response, HarmonicResponse)
        self.assertGreater(len(response.waveform), 0)
        self.assertIn("Reality", response.structured_text)
        self.assertGreaterEqual(len(response.structured_text.split()), len(text.split()))
        self.assertGreater(response.structured_text.split().count("resonance"), 1)

    def test_compression_mode_highlights_high_intensity_words(self) -> None:
        text = "Consciousness emerging from vibrational field interactions"
        settings = HarmonicSettings(
            waveform="sine",
            resonance_factor=2.0,
            compression=True,
            phase_modulation=True,
            harmonic_scaling=1.3,
        )

        response = harmonic_cognition(text, settings=settings)

        emphasised = [word for word in response.structured_text.split() if word.startswith("*")]
        self.assertTrue(emphasised)
        self.assertLessEqual(len(response.interpretive_layers), 3)
        self.assertTrue(all(layer.startswith("[") for layer in response.interpretive_layers))


if __name__ == "__main__":
    unittest.main()

