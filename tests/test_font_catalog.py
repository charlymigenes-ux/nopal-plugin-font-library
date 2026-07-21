import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = "ñÑáéíóúüÁÉÍÓÚÜ¿¡äöÄÖßàâæçèêëîïôœùûÿÀÂÆÇÈÊËÎÏÔŒÙÛŸãõÃÕ"


def u16(data, offset):
    return struct.unpack_from(">H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from(">I", data, offset)[0]


def covered_codepoints(data, required):
    table_count = u16(data, 4)
    cmap_offset = None
    for index in range(table_count):
        offset = 12 + index * 16
        if data[offset:offset + 4] == b"cmap":
            cmap_offset = u32(data, offset + 8)
            break
    if cmap_offset is None:
        return set()

    covered = set()
    record_count = u16(data, cmap_offset + 2)
    for index in range(record_count):
        record = cmap_offset + 4 + index * 8
        platform = u16(data, record)
        if platform not in (0, 3):
            continue
        subtable = cmap_offset + u32(data, record + 4)
        format_number = u16(data, subtable)
        if format_number == 12:
            group_count = u32(data, subtable + 12)
            for group in range(group_count):
                group_offset = subtable + 16 + group * 12
                start, end = u32(data, group_offset), u32(data, group_offset + 4)
                covered.update(codepoint for codepoint in required if start <= codepoint <= end)
        elif format_number == 4:
            segment_count = u16(data, subtable + 6) // 2
            end_base = subtable + 14
            start_base = end_base + 2 * segment_count + 2
            for segment in range(segment_count):
                start = u16(data, start_base + 2 * segment)
                end = u16(data, end_base + 2 * segment)
                covered.update(codepoint for codepoint in required if start <= codepoint <= end)
    return covered


class FontCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "fonts" / "catalog.json").read_text(encoding="utf-8"))

    def test_catalog_contains_twenty_unique_ofl_fonts(self):
        self.assertEqual(len(self.catalog), 20)
        self.assertEqual(len({font["id"] for font in self.catalog}), 20)
        self.assertTrue(all(font["license"] == "OFL-1.1" for font in self.catalog))

    def test_every_font_and_license_is_bundled(self):
        for font in self.catalog:
            folder = ROOT / "fonts" / font["directory"]
            self.assertTrue((folder / font["file"]).is_file(), font["name"])
            license_path = folder / "OFL.txt"
            self.assertTrue(license_path.is_file(), font["name"])
            self.assertIn("SIL OPEN FONT LICENSE", license_path.read_text(encoding="utf-8"), font["name"])

    def test_all_fonts_cover_five_nopal_languages(self):
        required = {ord(character) for character in REQUIRED}
        for font in self.catalog:
            path = ROOT / "fonts" / font["directory"] / font["file"]
            covered = covered_codepoints(path.read_bytes(), required)
            missing = "".join(character for character in REQUIRED if ord(character) not in covered)
            self.assertFalse(missing, f"{font['name']} lacks: {missing}")


if __name__ == "__main__":
    unittest.main()

