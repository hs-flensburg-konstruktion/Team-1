from pathlib import Path
import tempfile
import unittest

from otoskop.protocol import MAX_JPEG, MjpegParser, device_urls, save_photo


JPEG = b"\xff\xd8fake\r\n--otoskop_frame\r\nimage\xff\xd9"


def part(data=JPEG):
    return b"--otoskop_frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(data)).encode() + b"\r\n\r\n" + data + b"\r\n"


class ProtocolTests(unittest.TestCase):
    def test_arbitrary_network_fragmentation(self):
        data = part() * 3
        for width in (1, 2, 7, 64, len(data)):
            parser, frames = MjpegParser(), []
            for offset in range(0, len(data), width):
                frames.extend(parser.feed(data[offset:offset + width]))
            self.assertEqual(frames, [JPEG] * 3)

    def test_corrupt_and_unbounded_streams_are_rejected(self):
        for data in (b"x" * 8193, b"Content-Type: text/plain\r\n\r\n",
                     f"Content-Length: {MAX_JPEG + 1}\r\n\r\n".encode(),
                     b"Content-Length: 6\r\n\r\nnotjpg"):
            with self.subTest(data=data[:40]), self.assertRaises(ValueError):
                MjpegParser().feed(data)

    def test_address_validation(self):
        self.assertEqual(device_urls("192.168.4.1"), ("http://192.168.4.1", "http://192.168.4.1:81/stream"))
        self.assertEqual(device_urls("http://localhost:8080/"), ("http://localhost:8080", "http://localhost:81/stream"))
        self.assertEqual(device_urls("http://[::1]:8080"), ("http://[::1]:8080", "http://[::1]:81/stream"))
        for value in ("", "http://", "https://192.168.4.1", "host/path", "host?q=1",
                      "host#frag", "user:secret@host", "host:99999", "a b", "host\\path"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                device_urls(value)

    def test_photo_files_remain_unique_and_demo_is_marked(self):
        with tempfile.TemporaryDirectory() as folder:
            first = save_photo(Path(folder) / "photos", JPEG)
            second = save_photo(first.parent, JPEG)
            demo = save_photo(first.parent, JPEG, demo=True)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), JPEG)
            self.assertEqual(second.read_bytes(), JPEG)
            self.assertTrue(demo.name.startswith("DEMO_"))
            self.assertEqual(len(list(first.parent.glob("*.jpg"))), 3)
            with self.assertRaises(ValueError):
                save_photo(first.parent, b"partial")
            self.assertEqual(len(list(first.parent.glob("*.jpg"))), 3)


if __name__ == "__main__":
    unittest.main()
