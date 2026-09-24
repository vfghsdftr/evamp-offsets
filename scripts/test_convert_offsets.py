import unittest
from convert_offsets import convert

HEADER = '''// Roblox Version : version-2366ba214ec740ca
// Total Offsets : 2
#pragma once
namespace Offsets {
    inline std::string ClientVersion = "version-2366ba214ec740ca";
    namespace Example {
        inline constexpr uintptr_t Position = 0x128;
        inline uintptr_t FirstMember = 0;
    }
}
'''


class ConversionTests(unittest.TestCase):
    def test_literals_and_zero_preserved(self):
        result = convert(HEADER)
        self.assertEqual(result["Offsets"]["Example"], {"Position": 296, "FirstMember": 0})
        self.assertEqual(result["Total Offsets"], 2)

    def test_output_is_deterministic(self):
        self.assertEqual(convert(HEADER), convert(HEADER))

    def test_hex_and_decimal(self):
        self.assertEqual(convert(HEADER.replace("0x128", "296"))["Offsets"], convert(HEADER)["Offsets"])

    def test_reject_expressions(self):
        with self.assertRaises(ValueError):
            convert(HEADER.replace("0x128", "system(1)"))

    def test_reject_negative(self):
        with self.assertRaises(ValueError):
            convert(HEADER.replace("0x128", "-1"))

    def test_reject_overflow(self):
        with self.assertRaises(ValueError):
            convert(HEADER.replace("0x128", "0xFFFFFFFF"))

    def test_reject_duplicate(self):
        with self.assertRaises(ValueError):
            convert(HEADER.replace("FirstMember", "Position"))

    def test_reject_incomplete_namespace(self):
        with self.assertRaises(ValueError):
            convert(HEADER.rstrip()[:-1])

    def test_reject_count_mismatch(self):
        with self.assertRaises(ValueError):
            convert(HEADER.replace("Total Offsets : 2", "Total Offsets : 3"))

    def test_reject_version_mismatch(self):
        with self.assertRaises(ValueError):
            convert(HEADER.replace("Roblox Version : version-2366ba214ec740ca", "Roblox Version : version-0000000000000001"))

    def test_reject_empty_or_unversioned(self):
        for text in ("#offsets", HEADER.replace('inline std::string ClientVersion = "version-2366ba214ec740ca";', "")):
            with self.assertRaises(ValueError):
                convert(text)

    def test_dumper_banner_and_trailing_comments(self):
        self.assertEqual(convert(HEADER.replace("// Roblox", "/* Roblox").replace("0x128;", "0x128; // position"))["Offsets"], convert(HEADER)["Offsets"])


if __name__ == "__main__":
    unittest.main()
