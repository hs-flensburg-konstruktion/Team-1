import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('detect', pathlib.Path(__file__).parents[1] / 'scripts/detect_port.py')
detect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detect)

def port(address, vid='303a', pid='1001', matching=False):
    return {'port': {'protocol': 'serial', 'address': address, 'properties': {'vid': vid, 'pid': pid}},
            'matching_boards': [{'fqbn': 'esp32:esp32:XIAO_ESP32S3'}] if matching else []}

class PortDetection(unittest.TestCase):
    def test_no_board(self):
        with self.assertRaises(ValueError):
            detect.choose_port({'detected_ports': [port('/dev/cu.Bluetooth-Incoming-Port')]}, [])

    def test_unique_rom_port(self):
        self.assertEqual(detect.choose_port({'detected_ports': [port('/dev/cu.usbmodem101')]}, []), '/dev/cu.usbmodem101')

    def test_xiao_preferred(self):
        self.assertEqual(detect.choose_port({'detected_ports': [port('/dev/cu.usbmodem101'), port('/dev/cu.usbmodem102', '0x2886', '0x0056')]}, []), '/dev/cu.usbmodem102')

    def test_match_by_fqbn(self):
        self.assertEqual(detect.choose_port({'detected_ports': [port('/dev/cu.custom', matching=True)]}, []), '/dev/cu.custom')

    def test_ambiguous(self):
        with self.assertRaises(ValueError):
            detect.choose_port({'detected_ports': [port('/dev/cu.usbmodem101'), port('/dev/cu.usbmodem102')]}, [])

    def test_fallback(self):
        self.assertEqual(detect.choose_port({}, ['/dev/cu.usbmodem101']), '/dev/cu.usbmodem101')

if __name__ == '__main__':
    unittest.main()
