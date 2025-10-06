import unittest

from code import HarmonicResponse, HarmonicSettings, harmonic_cognition


class HarmonicCognitionTests(unittest.TestCase):
    def test_waveform_controls_intensity_markup(self) -> None:
        text = "Reality operates through quantum harmonic resonance"
        settings = HarmonicSettings(
            waveform="polyphonic",
            resonance_factor=1.4,
            lyricism_mode=False,
            emotional_tuning="neutral",
        )

        response = harmonic_cognition(text, settings=settings)

        self.assertIsInstance(response, HarmonicResponse)
        self.assertEqual(len(response.waveform), len(text.split()))
        emphasised = [word for word in response.structured_text.split() if word.startswith("*")]
        self.assertTrue(emphasised)
        self.assertLessEqual(len(response.interpretive_layers), 3)
        self.assertTrue(all("polyphonic" in layer for layer in response.interpretive_layers))

    def test_lyricism_appends_tagline_and_layers(self) -> None:
        text = "Consciousness emerging from vibrational field interactions"
        settings = HarmonicSettings(
            waveform="legato",
            resonance_factor=0.8,
            lyricism_mode=True,
            emotional_tuning="uplifting",
        )

        response = harmonic_cognition(text, settings=settings)

        self.assertIn("melody ascends toward dawn", response.structured_text)
        self.assertLessEqual(len(response.interpretive_layers), 3)
        self.assertTrue(any("uplifting" in layer for layer in response.interpretive_layers))


if __name__ == "__main__":
    unittest.main()

