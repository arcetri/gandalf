#!/usr/bin/env python3

'''
    A set of unit tests for the 'gandalf' script.
'''

import csv
import unittest
import argparse
from unittest import mock

import gandalf


class TestViewSet(unittest.TestCase):
    '''
        A set of tests for ViewSet class.
    '''

    def test_setDefaultView(self):
        '''
            Test setDefaultView method.
        '''
        # Setup default view mock
        view = gandalf.ViewSet()
        callable_mock = mock.MagicMock()
        callable_mock.return_value = 42 # pseudorandom number out of my head
        view.setDefaultView(callable_mock)

        # Test basic functionality
        self.assertEqual(view(), 42)
        self.assertTrue(callable_mock.called)
        callable_mock.assert_called_with()

        # Test with some other args
        callable_mock.return_value = 1995 # another pseudorandom number
                                          # (that's why I prefer not to generate passwords myself)
        self.assertEqual(view(123, "cisco4ever", "MTUCI1LOVE"), 1995)
        callable_mock.assert_called_with(123, "cisco4ever", "MTUCI1LOVE")


    def test_hosts(self):
        '''
            Test hosts method.
        '''
        hosts = [
            {"ip": "10.12.13.14", "hostname": "foo", "domain": "bar.com"},
            {"ip": "10.12.13.1", "hostname": "mew", "domain": "bar.com"},
            {"ip": "127.12.13.14", "hostname": "solnishko-lu4istoe", "domain": "fred.com"},
            {"ip": "127.12.13.14", "hostname": "innopolis", "domain": "fred.com"}
        ]
        expected_output = "10.12.13.1 mew mew.bar.com\n" \
            "10.12.13.14 foo foo.bar.com\n" \
            "127.12.13.14 solnishko-lu4istoe solnishko-lu4istoe.fred.com innopolis innopolis.fred.com"
        self.assertEqual(gandalf.ViewSet.hosts(hosts), expected_output)


    def test_dns(self):
        '''
            Test dns method.
        '''
        # Sample list of hosts
        hosts = [
            {"ip": "10.12.13.14", "hostname": "foo-10", "resides_on": "foo"},
            {"ip": "10.12.13.1", "hostname": "mew-10", "resides_on": "mew"},
            {"ip": "127.12.13.14", "hostname": "solnishko-lu4istoe", "resides_on": "innopolis"},
            {"ip": "127.12.13.14", "hostname": "innopolis", "resides_on": "innopolis"}
        ]

        # Test 'addr' rendering (must be default)
        expected_output_addr = \
            "foo-10                  IN      A       10.12.13.14\n" \
            "innopolis               IN      A       127.12.13.14\n" \
            "mew-10                  IN      A       10.12.13.1\n" \
            "solnishko-lu4istoe      IN      A       127.12.13.14"
        self.assertEqual(gandalf.ViewSet.dns(hosts, "addr"), expected_output_addr)
        self.assertEqual(gandalf.ViewSet.dns(hosts), expected_output_addr)

        # Test 'cname' rendering
        expected_output_cname = \
            "foo-10                  IN      CNAME   foo\n" \
            "innopolis               IN      CNAME   innopolis\n" \
            "mew-10                  IN      CNAME   mew\n" \
            "solnishko-lu4istoe      IN      CNAME   innopolis"
        self.assertEqual(gandalf.ViewSet.dns(hosts, "cname"), expected_output_cname)

        # Assert that some other rendering type raises ValueError
        self.assertRaises(ValueError, gandalf.ViewSet.dns, hosts, "foobar")


    def test_rdns(self):
        '''
            Test dns method.
        '''
        # Sample list of hosts
        hosts = [
            {"ip": "10.12.13.3", "hostname": "foo-10", "domain": "bar.com"},
            {"ip": "10.12.13.1", "hostname": "mew-10", "domain": "bar.com"},
            {"ip": "10.12.13.2", "hostname": "solnishko-lu4istoe", "domain": "bar.com"},
        ]

        # Test general case functionality
        expected_output = \
            "1                       1d      IN      PTR     mew-10.bar.com.\n" \
            "2                       1d      IN      PTR     solnishko-lu4istoe.bar.com.\n" \
            "3                       1d      IN      PTR     foo-10.bar.com."
        self.assertEqual(gandalf.ViewSet.rdns(hosts), expected_output)

        # Host the case when duplicate IP addresses are present
        hosts_duplicates = [
            {"ip": "10.12.13.1", "hostname": "foo-11", "domain": "bar.com"},
            {"ip": "10.12.13.1", "hostname": "mew-11", "domain": "bar.com"},
        ]
        self.assertRaises(ValueError, gandalf.ViewSet.rdns, hosts_duplicates)


    def test_dhcp(self):
        '''
            Test dhcp method.
        '''
        # Sample list of hosts
        hosts = [
            {"hostname": "foo", "ip": "10.12.13.14", "mask": "8",
                "domain": "bar.com", "mac": "00:00:00:00:00:00"},
            {"hostname": "mew", "ip": "10.12.13.1", "mask": "8",
                "domain": "bar.com", "mac": "10:00:00:00:00:00"},
            {"hostname": "solnishko-lu4istoe", "ip": "130.12.13.14", "mask": "16",
                "domain": "bum.com", "mac": "20:00:00:00:00:00"},
            {"hostname": "innopolis", "ip": "192.168.42.16", "mask": "24",
                "domain": "go.com", "mac": "30:00:00:00:00:00"}
        ]

        # Test general case functionality
        expected_output = \
            'host foo { option host-name "foo.bar.com"; hardware ethernet 00:00:00:00:00:00; ' \
                'fixed-address 10.12.13.14; option broadcast-address 10.255.255.255; }\n' \
            'host innopolis { option host-name "innopolis.go.com"; hardware ethernet 30:00:00:00:00:00; ' \
                'fixed-address 192.168.42.16; option broadcast-address 192.168.42.255; }\n' \
            'host mew { option host-name "mew.bar.com"; hardware ethernet 10:00:00:00:00:00; ' \
                'fixed-address 10.12.13.1; option broadcast-address 10.255.255.255; }\n' \
            'host solnishko-lu4istoe { option host-name "solnishko-lu4istoe.bum.com"; ' \
                'hardware ethernet 20:00:00:00:00:00; ' \
                'fixed-address 130.12.13.14; option broadcast-address 130.12.255.255; }'
        self.assertEqual(gandalf.ViewSet.dhcp(hosts), expected_output)

        # Test without hostname
        expected_output_no_hostname = \
            'host foo { hardware ethernet 00:00:00:00:00:00; ' \
                'fixed-address 10.12.13.14; option broadcast-address 10.255.255.255; }'
        self.assertEqual(gandalf.ViewSet.dhcp(hosts[:1], with_hostname=False),
                         expected_output_no_hostname)

        # Test with router ip
        expected_output_router = \
            'host foo { option host-name "foo.bar.com"; hardware ethernet 00:00:00:00:00:00; ' \
                'fixed-address 10.12.13.14; option broadcast-address 10.255.255.255; ' \
                'option routers 173.36.253.1; }'
        self.assertEqual(gandalf.ViewSet.dhcp(hosts[:1], router_ip="173.36.253.1"),
                         expected_output_router)

        # Test with filename
        expected_output_filename = \
            'host foo { option host-name "foo.bar.com"; hardware ethernet 00:00:00:00:00:00; ' \
                'fixed-address 10.12.13.14; option broadcast-address 10.255.255.255; ' \
                'option filename "uefi-head/shim.efi"; }'
        self.assertEqual(gandalf.ViewSet.dhcp(hosts[:1], filename="uefi-head/shim.efi"),
                         expected_output_filename)


class TestTopLevelFunctions(unittest.TestCase):
    '''
        A set of tests for top level functions.
    '''

    def test_parse_csv(self):
        '''
            Test parse_csv function.
        '''
        pass


    def test_find_templates(self):
        '''
            Test find_templates function.
        '''
        pass


    def test_apply_dns_version_hack(self):
        '''
            Test apply_dns_version_hack function.
        '''
        pass


    def test_dns_changed(self):
        '''
            Test dns_changed function.
        '''
        pass


    def test_parse_dns_version(self):
        '''
            Test parse_dns_version function.
        '''
        pass


    def test_main(self):
        '''
            Test main function.
        '''
        pass


if __name__ == '__main__':
    unittest.main()
