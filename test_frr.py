import pytest
from unittest import TestCase
from new_frr import (
    _find_first_block,
    _find_elements,
    ConfigSectionNotFound,
    frr
    )

TEST_CASE_1 = [
    'hostname HOSTNAME',
    'password PASSWORD',
    'log file /var/log/isisd.log',
    '!',
    '!',
    'interface eth0',
    ' ip router isis SR',
    ' isis network point-to-point',
    '!',
    'interface eth1',
    ' ip router isis SR',
    '!',
    '!',
    'router isis SR',
    ' net 49.0000.0000.0000.0001.00',
    ' is-type level-1',
    ' topology ipv6-unicast',
    ' lsp-gen-interval 2',
    ' segment-routing on',
    ' segment-routing node-msd 8',
    ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
    ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
    '!',
    'line vty',
    ]

TEST_CASE_2 = [
    'hostname HOSTNAME',
    'password PASSWORD',
    'log file /var/log/isisd.log',
    '!',
    '!',
    'interface eth0',
    ' ip router isis SR',
    ' isis network point-to-point',
    '!',
    'interface eth0 vrf RED',
    ' ip router isis SRRED',
    ' isis network point-to-point',
    '!',
    'interface eth1',
    ' ip router isis SR',
    '!',
    'interface eth8 vrf BLUE',
    ' ip router isis SRBLUE',
    '!',
    '!',
    'router isis SR',
    ' net 49.0000.0000.0000.0001.00',
    ' is-type level-1',
    ' topology ipv6-unicast',
    ' lsp-gen-interval 2',
    ' segment-routing on',
    ' segment-routing node-msd 8',
    ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
    ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
    '!',
    'router isis SRRED vrf RED',
    ' net 49.0000.0001.0001.0001.00',
    ' is-type level-1',
    ' topology ipv6-unicast',
    ' lsp-gen-interval 2',
    ' segment-routing on',
    ' segment-routing node-msd 8',
    ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
    ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
    '!',
    'router isis SRBLUE vrf BLUE',
    ' net 49.0000.0002.0002.0002.00',
    ' is-type level-1',
    ' topology ipv6-unicast',
    ' lsp-gen-interval 2',
    ' segment-routing on',
    ' segment-routing node-msd 8',
    ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
    ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
    '!',
    'line vty',
    ]


class FindFirstBlock(TestCase):
    def test_find_valid_interface_eth0(self):
        test_config = TEST_CASE_2.copy()
        test1 = _find_first_block(test_config, "interface eth0", "!")
        self.assertEqual(test1, (5, 8))

    def test_find_valid_interface_eth1(self):
        test_config = TEST_CASE_2.copy()
        test2 = _find_first_block(test_config, "interface eth1", "!")
        self.assertEqual(test2, (13, 15))

    def test_find_valid_router_isis_sr(self):
        test_config = TEST_CASE_2.copy()
        test3 = _find_first_block(test_config, "router isis SR", "!")
        self.assertEqual(test3, (20, 29))

    def test_find_valid_interface_regex(self):
        test_config = TEST_CASE_2.copy()
        test3 = _find_first_block(test_config, "interface .*1", "!")
        self.assertEqual(test3, (13, 15))

    def test_find_valid_interface_regex_vrf_RED(self):
        test_config = TEST_CASE_2.copy()
        test3 = _find_first_block(test_config, "interface .* vrf RED", "!")
        self.assertEqual(test3, (9, 12))


    def test_find_valid_interface_regex_vrf_RED(self):
        test_config = TEST_CASE_2.copy()
        test3 = _find_first_block(test_config, "interface .* vrf BLUE", "!")
        self.assertEqual(test3, (16, 18))

    def test_find_invalid_fixed_blocks(self):
        test_config = TEST_CASE_2.copy()
        test1 = _find_first_block(test_config, "interface eth9", "!")
        self.assertEqual(test1, None)


class FindElements(TestCase):
    def test_find_interfaces(self):
        test_config = TEST_CASE_2.copy()
        test1 = _find_elements(test_config, r'interface eth\d+')
        self.assertEqual(test1, [5, 13])

    def test_find_interfaces_vrf(self):
        test_config = TEST_CASE_2.copy()
        test1 = _find_elements(test_config, r'interface eth\d+ vrf RED')
        self.assertEqual(test1, [9])


class RemoveSection(TestCase):
    def test_remove_router_isis_sr(self):
        test = frr(config=TEST_CASE_1.copy())
        test1 = test.modify_section("router isis SR")
        self.assertEqual(test1, 1)
        self.assertEqual(test.config, [
            'hostname HOSTNAME',
            'password PASSWORD',
            'log file /var/log/isisd.log',
            '!',
            '!',
            'interface eth0',
            ' ip router isis SR',
            ' isis network point-to-point',
            '!',
            'interface eth1',
            ' ip router isis SR',
            '!',
            '!',
            '!',
            'line vty',
            ])

    def test_remove_router_isis_sr_remove_stop_line(self):
        test = frr(config=TEST_CASE_1.copy())
        test1 = test.modify_section("router isis SR", remove_stop_mark=True)
        self.assertEqual(test1, 1)
        self.assertEqual(test.config, [
            'hostname HOSTNAME',
            'password PASSWORD',
            'log file /var/log/isisd.log',
            '!',
            '!',
            'interface eth0',
            ' ip router isis SR',
            ' isis network point-to-point',
            '!',
            'interface eth1',
            ' ip router isis SR',
            '!',
            '!',
            'line vty',
            ])

    def test_remove_interface_once(self):
        test = frr(config=TEST_CASE_1.copy())
        test1 = test.modify_section(r"interface eth\d+$", count=1)
        self.assertEqual(test1, 1)
        self.assertEqual(test.config, [
            'hostname HOSTNAME',
            'password PASSWORD',
            'log file /var/log/isisd.log',
            '!',
            '!',
            '!',
            'interface eth1',
            ' ip router isis SR',
            '!',
            '!',
            'router isis SR',
            ' net 49.0000.0000.0000.0001.00',
            ' is-type level-1',
            ' topology ipv6-unicast',
            ' lsp-gen-interval 2',
            ' segment-routing on',
            ' segment-routing node-msd 8',
            ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
            ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
            '!',
            'line vty',
        ])


    def test_remove_interface_once_with_removed_mark(self):
        test = frr(config=TEST_CASE_1.copy())
        test1 = test.modify_section(r"interface eth\d+$", remove_stop_mark=True, count=1)
        self.assertEqual(test1, 1)
        self.assertEqual(test.config, [
            'hostname HOSTNAME',
            'password PASSWORD',
            'log file /var/log/isisd.log',
            '!',
            '!',
            'interface eth1',
            ' ip router isis SR',
            '!',
            '!',
            'router isis SR',
            ' net 49.0000.0000.0000.0001.00',
            ' is-type level-1',
            ' topology ipv6-unicast',
            ' lsp-gen-interval 2',
            ' segment-routing on',
            ' segment-routing node-msd 8',
            ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
            ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
            '!',
            'line vty',
        ])

    def test_remove_interface_multiple_with_removed_mark(self):
        test = frr(TEST_CASE_1.copy())
        test1 = test.modify_section(r"interface eth\d+$", remove_stop_mark=True)
        self.assertEqual(test1, 2)
        self.assertEqual(test.config, [
            'hostname HOSTNAME',
            'password PASSWORD',
            'log file /var/log/isisd.log',
            '!',
            '!',
            '!',
            'router isis SR',
            ' net 49.0000.0000.0000.0001.00',
            ' is-type level-1',
            ' topology ipv6-unicast',
            ' lsp-gen-interval 2',
            ' segment-routing on',
            ' segment-routing node-msd 8',
            ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
            ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
            '!',
            'line vty',
        ])

    def test_remove_nonexisting_line(self):
        test = frr(TEST_CASE_1.copy())
        test1 = test.modify_section("unknown config section")
        self.assertEqual(test1, 0)

    def test_replace_config_with_itself(self):
        test = frr(TEST_CASE_1.copy())
        test1 = test.modify_section('interface eth0', replacement='interface eth0\n THIS IS REPLACED')
        self.assertEqual(test1, 1)
        self.assertEqual(test.config, [
            'hostname HOSTNAME',
            'password PASSWORD',
            'log file /var/log/isisd.log',
            '!',
            '!',
            'interface eth0',
            ' THIS IS REPLACED',
            '!',
            'interface eth1',
            ' ip router isis SR',
            '!',
            '!',
            'router isis SR',
            ' net 49.0000.0000.0000.0001.00',
            ' is-type level-1',
            ' topology ipv6-unicast',
            ' lsp-gen-interval 2',
            ' segment-routing on',
            ' segment-routing node-msd 8',
            ' segment-routing prefix 10.1.1.1/32 index 100 explicit-null',
            ' segment-routing prefix 2001:db8:1000::1/128 index 101 explicit-null',
            '!',
            'line vty',
            ])
