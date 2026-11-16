"""
Unit tests for subnet_calc.py

Run from the project folder:
    python -m unittest discover -s scripts -v
"""
import io
import ipaddress
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import subnet_calc as sc


class TestIPv4Info(unittest.TestCase):
    def test_host_in_slash26(self):
        info = sc.describe("192.168.10.77/26")
        self.assertEqual(info["Network"], "192.168.10.64/26")
        self.assertEqual(info["Subnet mask"], "255.255.255.192")
        self.assertEqual(info["Wildcard mask"], "0.0.0.63")
        self.assertEqual(info["Broadcast"], "192.168.10.127")
        self.assertEqual(info["First usable"], "192.168.10.65")
        self.assertEqual(info["Last usable"], "192.168.10.126")
        self.assertEqual(info["Usable hosts"], "62")
        self.assertEqual(info["Block size"], "64 (octet 4)")
        self.assertEqual(info["Mask (binary)"], "11111111.11111111.11111111.11000000")
        self.assertIn("host address", info["Address"])

    def test_dotted_mask_input(self):
        info = sc.describe("192.168.45.130 255.255.255.224")
        self.assertEqual(info["Network"], "192.168.45.128/27")
        self.assertEqual(info["Broadcast"], "192.168.45.159")

    def test_network_and_broadcast_roles(self):
        self.assertIn("network address", sc.describe("10.1.1.0/24")["Address"])
        self.assertIn("broadcast address", sc.describe("10.1.1.255/24")["Address"])

    def test_block_size_third_octet(self):
        info = sc.describe("10.20.37.200/21")
        self.assertEqual(info["Network"], "10.20.32.0/21")
        self.assertEqual(info["Broadcast"], "10.20.39.255")
        self.assertEqual(info["Usable hosts"], "2,046")
        self.assertEqual(info["Block size"], "8 (octet 3)")

    def test_point_to_point_and_host_routes(self):
        self.assertEqual(sc.usable_hosts(ipaddress.ip_network("10.0.0.0/30")), 2)
        self.assertEqual(sc.usable_hosts(ipaddress.ip_network("10.0.0.0/31")), 2)
        self.assertEqual(sc.usable_hosts(ipaddress.ip_network("10.0.0.1/32")), 1)

    def test_class_and_type(self):
        self.assertEqual(sc.describe("172.16.5.1/16")["Class"], "B (default /16)")
        self.assertEqual(sc.describe("172.16.5.1/16")["Type"], "Private (RFC 1918)")
        self.assertIn("RFC 5737", sc.describe("203.0.113.9/24")["Type"])
        self.assertIn("CGNAT", sc.describe("100.64.1.1/10")["Type"])
        self.assertEqual(sc.describe("9.9.9.9/32")["Type"], "Public")


class TestIPv6(unittest.TestCase):
    def test_info(self):
        info = sc.describe("2001:db8:acad:10::1/64")
        self.assertEqual(info["Network"], "2001:db8:acad:10::/64")
        self.assertEqual(info["Expanded"], "2001:0db8:acad:0010:0000:0000:0000:0001")
        self.assertIn("RFC 3849", info["Type"])

    def test_slash48_has_65536_lans(self):
        info = sc.describe("2001:db8:acad::/48")
        self.assertEqual(info["/64 subnets inside"], "2^16 = 65,536")

    def test_compression_tie_uses_leftmost_run(self):
        addr = ipaddress.IPv6Address("2001:0db8:0000:0000:00a0:0000:0000:0001")
        self.assertEqual(addr.compressed, "2001:db8::a0:0:0:1")

    def test_link_local_and_ula(self):
        self.assertEqual(sc.describe("fe80::1/64")["Type"], "Link-local")
        self.assertIn("ULA", sc.describe("fd00:1::1/64")["Type"])

    def test_eui64(self):
        addr, steps = sc.eui64("2001:db8:acad:10::/64", "00:1A:2B:3C:4D:5E")
        self.assertEqual(str(addr), "2001:db8:acad:10:21a:2bff:fe3c:4d5e")
        self.assertEqual(dict(steps)["5. Interface ID"], "021a:2bff:fe3c:4d5e")

    def test_eui64_cisco_mac_format(self):
        addr, _ = sc.eui64("2001:db8:acad:10::/64", "001a.2b3c.4d5e")
        self.assertEqual(str(addr), "2001:db8:acad:10:21a:2bff:fe3c:4d5e")

    def test_eui64_rejects_non_64(self):
        with self.assertRaises(ValueError):
            sc.eui64("2001:db8::/48", "00:1A:2B:3C:4D:5E")


class TestSplitAndVlsm(unittest.TestCase):
    def test_split(self):
        subnets = sc.split("192.168.10.0/24", 26)
        self.assertEqual([str(s) for s in subnets],
                         ["192.168.10.0/26", "192.168.10.64/26", "192.168.10.128/26", "192.168.10.192/26"])

    def test_split_rejects_shorter_prefix(self):
        with self.assertRaises(ValueError):
            sc.split("192.168.10.0/24", 23)

    def test_prefix_for_hosts(self):
        cases = {1: 30, 2: 30, 3: 29, 10: 28, 25: 27, 50: 26, 100: 25, 200: 24, 254: 24, 255: 23, 500: 23}
        for hosts, prefix in cases.items():
            with self.subTest(hosts=hosts):
                self.assertEqual(sc.prefix_for_hosts(hosts), prefix)

    def test_addressing_plan_vlsm(self):
        """Must match the IPv4 table in addressing-plan.md."""
        reqs = [("WAN-HQ-BR", 2), ("HQ-SALES", 200), ("BR-IT", 25), ("HQ-IT", 100),
                ("MGMT", 10), ("BR-SALES", 50)]
        allocations, free = sc.vlsm("172.16.0.0/22", reqs)
        self.assertEqual([(n, str(s)) for n, _, s in allocations], [
            ("HQ-SALES", "172.16.0.0/24"),
            ("HQ-IT", "172.16.1.0/25"),
            ("BR-SALES", "172.16.1.128/26"),
            ("BR-IT", "172.16.1.192/27"),
            ("MGMT", "172.16.1.224/28"),
            ("WAN-HQ-BR", "172.16.1.240/30"),
        ])
        self.assertEqual([str(f) for f in free], ["172.16.1.244/30", "172.16.1.248/29", "172.16.2.0/23"])

    def test_vlsm_out_of_space(self):
        with self.assertRaises(ValueError):
            sc.vlsm("192.168.1.0/24", [("BIG", 200), ("ALSO-BIG", 100)])

    def test_parse_requirement(self):
        self.assertEqual(sc.parse_requirement("SALES=50"), ("SALES", 50))
        with self.assertRaises(ValueError):
            sc.parse_requirement("SALES50")


class TestQuizAndCli(unittest.TestCase):
    def test_quiz_scores_correct_answers(self):
        # Replay the same random draw to compute the right answers
        probe = random.Random(7)
        pools = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
        pool = probe.choice(pools)
        addr = pool.network_address + probe.randrange(pool.num_addresses)
        net = ipaddress.ip_interface(f"{addr}/{probe.randint(17, 30)}").network
        answers = iter([str(net.network_address), str(net.broadcast_address), str(sc.usable_hosts(net))])

        with redirect_stdout(io.StringIO()):
            score = sc.quiz(1, random.Random(7), ask=lambda _: next(answers))
        self.assertEqual(score, 1)

    def test_cli_returns_error_code_on_bad_input(self):
        with redirect_stdout(io.StringIO()), mock.patch("sys.stderr", new=io.StringIO()):
            self.assertEqual(sc.main(["info", "300.1.1.1/24"]), 2)

    def test_cli_vlsm_runs(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(sc.main(["vlsm", "10.0.0.0/24", "A=50", "B=20"]), 0)
        self.assertIn("10.0.0.0/26", out.getvalue())


if __name__ == "__main__":
    unittest.main()
