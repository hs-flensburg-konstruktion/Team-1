from string import Formatter
import unittest

from otoskop.i18n import SOURCE, TEXT, Translator


class TranslationTests(unittest.TestCase):
    def test_both_languages_have_the_same_placeholders(self):
        for key, (de, en) in TEXT.items():
            with self.subTest(key=key):
                self.assertTrue(de.strip())
                self.assertTrue(en.strip())
                fields = lambda value: {field for _, field, _, _ in Formatter().parse(value) if field}
                self.assertEqual(fields(de), fields(en))

    def test_protocol_messages_translate_without_touching_device_codes(self):
        tr = Translator("en")
        for de, en in SOURCE.items():
            self.assertEqual(tr.source(de), en)
        message = "Otoskop nicht erreichbar. WLAN-Verbindung und Geräteadresse prüfen. Erneuter Versuch läuft automatisch."
        self.assertIn("Retrying automatically", tr.source(message))
        self.assertIn("Lighting:", tr.source("LED-Steuerung: LED-Steuerung beschäftigt."))
        self.assertIn("HTTP 503", tr.source("Das Otoskop meldet HTTP 503."))
        self.assertIn("ESP_ERR_NOT_FOUND", tr.source("Kamera nicht gestartet: ESP_ERR_NOT_FOUND. Kabel prüfen."))
        self.assertEqual(Translator("de").source(message), message)
        self.assertEqual(Translator("unsupported").language, "de")
