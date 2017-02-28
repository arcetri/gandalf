#!/usr/bin/env python3

'''
    A set of unit tests for the 'gandalf' script.
'''

import csv
import yaml
import mako
import unittest
import argparse
import datetime
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

        # Test when default view is not set
        view = gandalf.ViewSet()
        self.assertRaises(ValueError, view)


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
            {"hostname": "foo", "ip": "10.12.13.14", "mask": 8,
                "domain": "bar.com", "mac": "00:00:00:00:00:00"},
            {"hostname": "mew", "ip": "10.12.13.1", "mask": 8,
                "domain": "bar.com", "mac": "10:00:00:00:00:00"},
            {"hostname": "solnishko-lu4istoe", "ip": "130.12.13.14", "mask": 16,
                "domain": "bum.com", "mac": "20:00:00:00:00:00"},
            {"hostname": "innopolis", "ip": "192.168.42.16", "mask": 24,
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

    @mock.patch('gandalf.open')
    @mock.patch('gandalf.csv.DictReader')
    def test_parse_csv(self, DictReader_mock, open_mock):
        '''
            Test parse_csv function.
        '''
        # Shortcut for readlines mock
        readlines_mock = open_mock().__enter__().readlines
        open_mock.reset_mock()

        # Test that it tried to open the file
        readlines_mock.return_value = ["foo,bar,mew"]
        DictReader_mock.return_value = []
        self.assertEqual(gandalf.parse_csv("foobar_file"), [])
        self.assertTrue(readlines_mock.called)
        open_mock.assert_called_once_with("foobar_file", "r")

        # Test column name transform
        DictReader_mock.return_value = [{"FOO": "1", "foo bar": "2", "  mew\t ": "3"}]
        self.assertEqual(gandalf.parse_csv("foobar_file"),
            [{"foo": "1", "foo_bar": "2", "mew": "3"}])

        # Test column value validators and transformers
        # hostname and domain:
        for col in ("hostname", "domain"):
            for invalid_value in ("", "   ", "\t", "   \t  \t    "):
                DictReader_mock.return_value = [{col: invalid_value}]
                self.assertRaises(gandalf.CsvIntegrityError, gandalf.parse_csv, "file")
            DictReader_mock.return_value = [{col: " fooAV7v 0g3702$$%5   "}]
            self.assertEqual(gandalf.parse_csv("file"), [{col: "fooAV7v 0g3702$$%5"}])

        # vlan:
        for invalid_value in ("0", "4096", "24353", "-1255"):
            DictReader_mock.return_value = [{"vlan": invalid_value}]
            self.assertRaises(gandalf.CsvIntegrityError, gandalf.parse_csv, "file")
        DictReader_mock.return_value = [{"vlan": "500"}, {"vlan": ""}, {"vlan": "\t "}]
        self.assertEqual(gandalf.parse_csv("file"), [{"vlan": 500},{"vlan": None},{"vlan": None}])

        # ip:
        for invalid_value in ("", " \t  ", "not_valid_ip", "192.156.0",
                              "123.34.53.33.3", "145.256.95.311", "10.10.-5.4"):
            DictReader_mock.return_value = [{"ip": invalid_value}]
            self.assertRaises(gandalf.CsvIntegrityError, gandalf.parse_csv, "file")
        DictReader_mock.return_value = [{"ip": "10.10.0.3"}, {"ip": "  192.168.3.4\t"}]
        self.assertEqual(gandalf.parse_csv("file"), [{"ip": "10.10.0.3"},{"ip": "192.168.3.4"}])

        # mask:
        for invalid_value in ("", "     ", "-1", "33", "345"):
            DictReader_mock.return_value = [{"mask": invalid_value}]
            self.assertRaises(gandalf.CsvIntegrityError, gandalf.parse_csv, "file")
        DictReader_mock.return_value = [{"mask": "8"}, {"mask": "  16 \t "}]
        self.assertEqual(gandalf.parse_csv("file"), [{"mask": 8},{"mask": 16}])

        # mac:
        for invalid_value in ("not_mac", "ab:ab:ab:cx:df:eg"):
            DictReader_mock.return_value = [{"mac": invalid_value}]
            self.assertRaises(gandalf.CsvIntegrityError, gandalf.parse_csv, "file")
        DictReader_mock.return_value = [{"mac": "10:10:10:10:10:10"}, {"mac": " ab:bc:cd:de:ef:f0\t "}]
        self.assertEqual(gandalf.parse_csv("file"), [{"mac": "10:10:10:10:10:10"},{"mac": "ab:bc:cd:de:ef:f0"}])

        # entity_type:
        for invalid_value in ("", "  ", "\t", "foobar", "comp_", "15246"):
            DictReader_mock.return_value = [{"entity_type": invalid_value}]
            self.assertRaises(gandalf.CsvIntegrityError, gandalf.parse_csv, "file")
        DictReader_mock.return_value = [{"entity_type": x} for x in
                ["comp", "head ", "\thardware", "fi  ", "alias", "cimc"]]
        self.assertEqual(gandalf.parse_csv("file"), [{"entity_type": x} for x in
                ["comp", "head", "hardware", "fi", "alias", "cimc"]])

        # Test gandalf_ignore column:
        DictReader_mock.return_value = [
            {"hostname": "foo0", "gandalf_ignore": ""},
            {"hostname": "foo1", "gandalf_ignore": "  "},
            {"hostname": "foo2", "gandalf_ignore": "  \t"},
            {"hostname": "bar0", "gandalf_ignore": "0"},
            {"hostname": "bar1", "gandalf_ignore": "-"},
            {"hostname": "bar2", "gandalf_ignore": "no"},
            {"hostname": "bar3", "gandalf_ignore": "yes"}
        ]
        self.assertEqual(gandalf.parse_csv("file"), [
            {"hostname": "foo{}".format(i), "gandalf_ignore": ""} for i in range(3)
        ])

        # Test comments stripping
        readlines_mock.return_value = [
            "foo,bar,mew",
            "# first easy comment",
            "  # second one with some preceeding spaces",
            "\"#quoted string comment, contains commas\"",
            "  \t\"\t # quoted string, some spaces and tabs preceeding\"",
            "1,2,3"
        ]
        DictReader_mock.reset_mock()
        gandalf.parse_csv("file")
        DictReader_mock.assert_called_once_with(["foo,bar,mew", "1,2,3"])


    @mock.patch('gandalf.os.path.isdir')
    @mock.patch('gandalf.os.walk')
    def test_find_templates(self, walk_mock, isdir_mock):
        '''
            Test find_templates function.
        '''
        # mock function for os.path.isdir:
        # if file path ends with "dir", than it is directory
        isdir_mock.side_effect = lambda s: s.endswith("dir") or s.endswith("/")

        # Test case when inpath, outpath and dnspath are all files
        self.assertEqual(list(gandalf.find_templates("infile", "outfile", "dnsfile")),
            [("infile", "outfile", "dnsfile")])

        # Inpath is a file, outpath and dnspath are directories
        self.assertEqual(list(gandalf.find_templates("infile", "outdir", "dnsdir")),
            [("infile", "outdir/infile", "dnsdir/infile")])

        # Inpath and outpath are files, dnspath is a directory
        self.assertEqual(list(gandalf.find_templates("infile", "outfile", "dnsdir")),
            [("infile", "outfile", "dnsdir/infile")])

        # Inpath and dnspath are files, outpath is a directory
        self.assertEqual(list(gandalf.find_templates("infile", "outdir", "dnsfile")),
            [("infile", "outdir/infile", "dnsfile")])

        # Test that slash at the and of directory name doesn't break output
        self.assertEqual(list(gandalf.find_templates("infile", "outdir/", "dnsdir/")),
            [("infile", "outdir/infile", "dnsdir/infile")])

        # Test when infile is a directory.
        # Refer to os.walk documentation on the structure of os.walk call result.
        walk_mock.return_value = [
            ("templates_dir", ["foo_dir", "bar_dir"], ["zero_template"]),
            ("templates_dir/foo_dir", [], ["first_template", "second_template"]),
            ("templates_dir/bar_dir", ["mew_dir"], ["third_template"]),
            ("templates_dir/bar_dir/mew_dir", [], ["fourth_template"])
        ]
        expected_output = [
            ("templates_dir/zero_template", "output_dir/zero_template", "dns_dir/zero_template"),
            ("templates_dir/foo_dir/first_template", "output_dir/foo_dir/first_template",
                "dns_dir/foo_dir/first_template"),
            ("templates_dir/foo_dir/second_template", "output_dir/foo_dir/second_template",
                "dns_dir/foo_dir/second_template"),
            ("templates_dir/bar_dir/third_template", "output_dir/bar_dir/third_template",
                "dns_dir/bar_dir/third_template"),
            ("templates_dir/bar_dir/mew_dir/fourth_template", "output_dir/bar_dir/mew_dir/fourth_template",
                "dns_dir/bar_dir/mew_dir/fourth_template"),
        ]
        self.assertEqual(list(gandalf.find_templates("templates_dir", "output_dir", "dns_dir")),
            expected_output)
        self.assertEqual(list(gandalf.find_templates("templates_dir/", "output_dir", "dns_dir")),
            expected_output)


    @mock.patch('gandalf.open')
    @mock.patch('gandalf.dns_changed')
    @mock.patch('gandalf.parse_dns_version')
    @mock.patch('gandalf.datetime.datetime')
    def test_apply_dns_version_hack(self, datetime_mock, dns_version_mock,
                                    dns_changed_mock, open_mock):
        '''
            Test apply_dns_version_hack function.
        '''
        # Shortcut for read mock
        read_mock = open_mock().__enter__().read
        open_mock.reset_mock()

        # Shortcut for datetime.datetime.now mock
        now_mock = datetime_mock.now
        gandalf.datetime.datetime.strftime.side_effect = \
            lambda d, f: "{:04}{:02}{:02}".format(d["year"], d["month"], d["day"])

        # Test case when old version of file is smaller and file not changed
        read_mock.return_value = "other_dns_contents"
        now_mock.return_value = {"year": 2017, "month": 1, "day": 1}
        dns_version_mock.return_value = 2016123100
        dns_changed_mock.return_value = False
        dns_contents = "foobar\n" + gandalf.DNS_HACK_ANCHOR + "\nbarfoo"
        self.assertEqual(gandalf.apply_dns_version_hack(dns_contents, "oldfile"),
            "foobar\n2016123100\nbarfoo")
        open_mock.assert_called_once_with("oldfile", "r")
        now_mock.assert_called_once_with()
        dns_version_mock.assert_called_once_with("other_dns_contents")
        dns_changed_mock.assert_called_once_with(dns_contents, "other_dns_contents")

        # Test case when old version of file is smaller and file changed
        dns_changed_mock.return_value = True
        self.assertEqual(gandalf.apply_dns_version_hack(dns_contents, "oldfile"),
            "foobar\n2017010100\nbarfoo")

        # Test case when old version of file is bigger and file changed
        dns_version_mock.return_value = 2017010130
        self.assertEqual(gandalf.apply_dns_version_hack(dns_contents, "oldfile"),
            "foobar\n2017010131\nbarfoo")

        # Test case when old version of file is bigger and file not changed
        dns_changed_mock.return_value = False
        self.assertEqual(gandalf.apply_dns_version_hack(dns_contents, "oldfile"),
            "foobar\n2017010130\nbarfoo")

        # Test case when open raises IOError
        open_mock.side_effect = IOError()
        self.assertEqual(gandalf.apply_dns_version_hack(dns_contents, "oldfile"),
            "foobar\n2017010100\nbarfoo")

        # Test case when open raises ValueError
        open_mock.side_effect = ValueError()
        self.assertEqual(gandalf.apply_dns_version_hack(dns_contents, "oldfile"),
            "foobar\n2017010100\nbarfoo")


    def test_dns_changed(self):
        '''
            Test dns_changed function.
        '''
        # Test on identical strings
        self.assertFalse(gandalf.dns_changed("my_dns_config", "my_dns_config"))

        # Test on strings that have different spacing
        self.assertFalse(gandalf.dns_changed("  my_dns_config ", "\tmy_dns_config    "))

        # Test on strings that have different comments
        self.assertFalse(gandalf.dns_changed("my_dns_config ; comment 1", "my_dns_config ; my comment 2"))

        # Test on strings that have different line splitting
        self.assertFalse(gandalf.dns_changed("my config \n continues", "my \n config continues"))

        # Test on different content
        self.assertTrue(gandalf.dns_changed("my_dns_config", "other_dns_config"))


    def test_parse_dns_version(self):
        '''
            Test parse_dns_version function.
        '''
        # Test on string with a single hack comment
        self.assertEqual(gandalf.parse_dns_version("abc\nsomething 637237337" + gandalf.DNS_HACK_COMMENT),
                         637237337)

        # Test on string with lwo hack comments
        self.assertEqual(gandalf.parse_dns_version(
            "def\nsomething 637237337 {0}\nelse 56474575 {0}".format(gandalf.DNS_HACK_COMMENT)),
                637237337)

        # Test on string with no comment
        self.assertEqual(gandalf.parse_dns_version("nothing to be parsed"), 0)

        # Test when comment is present, but no version
        self.assertEqual(gandalf.parse_dns_version(gandalf.DNS_HACK_COMMENT), 0)

        # Test when comment is present, but preceeding string is not an int
        self.assertEqual(gandalf.parse_dns_version("garbage" + gandalf.DNS_HACK_COMMENT), 0)


    @mock.patch('gandalf.open')
    @mock.patch('gandalf.logging')
    @mock.patch('gandalf.sys.exit')
    @mock.patch('gandalf.parse_csv')
    @mock.patch('gandalf.yaml.load')
    @mock.patch('gandalf.os.makedirs')
    @mock.patch('gandalf.tinydb.TinyDB')
    @mock.patch('gandalf.find_templates')
    @mock.patch('gandalf.apply_dns_version_hack')
    @mock.patch('gandalf.mako.template.Template')
    @mock.patch('gandalf.argparse.ArgumentParser')
    def test_main(self, ArgumentParser_mock, Template_mock, apply_dns_version_hack_mock,
                  find_templates_mock, TinyDB_mock, makedirs_mock, yaml_load_mock,
                  parse_csv_mock, exit_mock, logging_mock, open_mock):
        '''
            Test main function.
        '''
        # Shortcut for resetting all mocks
        def reset_all_mocks():
            for mock in [ArgumentParser_mock, Template_mock, apply_dns_version_hack_mock,
                         find_templates_mock, TinyDB_mock, makedirs_mock, yaml_load_mock,
                         parse_csv_mock, exit_mock, logging_mock, open_mock]:
                mock.reset_mock()

        # Shortcut for checking error exit
        def assert_error_exit():
            self.assertTrue(exit_mock.called)
            self.assertTrue(exit_mock.call_args_list[-1][0][0] > 0)
            self.assertTrue(logging_mock.fatal.called)

        # Shortcut for command-line arguments mock
        args_mock = ArgumentParser_mock().parse_args()
        ArgumentParser_mock.reset_mock()

        # Test run
        gandalf.main()
        exit_mock.assert_called_once_with(0)
        reset_all_mocks()

        # parse_csv throws exception
        args_mock.csvfile = "file.csv"
        for Exc in [IOError, csv.Error, gandalf.CsvIntegrityError]:
            parse_csv_mock.side_effect = Exc()
            gandalf.main()
            parse_csv_mock.assert_called_once_with("file.csv")
            assert_error_exit()
            reset_all_mocks()
        parse_csv_mock.side_effect = None

        # open() on args.var throws exception
        args_mock.var = "varfile.yaml"
        open_mock.side_effect = IOError()
        gandalf.main()
        open_mock.assert_called_once_with("varfile.yaml", "r")
        assert_error_exit()
        reset_all_mocks()
        open_mock.side_effect = None

        # yaml.load throws exception
        yaml_load_mock.side_effect = yaml.error.YAMLError()
        gandalf.main()
        assert_error_exit()
        reset_all_mocks()
        yaml_load_mock.side_effect = None

        # mako.template.Template throws exception
        find_templates_mock.return_value = [("templates/infile.mako", "rendered/outfile.mako", "dns/dnsfile.mako")]
        args_mock.var = None
        for Exc in [IOError, mako.exceptions.MakoException]:
            Template_mock.side_effect = Exc()
            gandalf.main()
            Template_mock.assert_called_once_with(filename="templates/infile.mako")
            self.assertTrue(logging_mock.error.called)
            reset_all_mocks()
        Template_mock.side_effect = None

        # Template rendering throws an exception
        Template_mock().render_unicode.side_effect = Exception()
        gandalf.main()
        self.assertTrue(logging_mock.error.called)
        reset_all_mocks()
        Template_mock().render_unicode.side_effect = None

        # Test that DNS version hack is applied
        Template_mock().render_unicode.return_value = gandalf.DNS_HACK_ANCHOR
        gandalf.main()
        apply_dns_version_hack_mock.assert_called_once_with(gandalf.DNS_HACK_ANCHOR, "dns/dnsfile")
        reset_all_mocks()

        # Test that os.makedirs is called if neccesary
        # and that OSError is handled
        makedirs_mock.side_effect = OSError()
        gandalf.main()
        makedirs_mock.assert_called_once_with("rendered", exist_ok=True)
        self.assertTrue(logging_mock.error.called)
        reset_all_mocks()
        makedirs_mock.side_effect = None

        # Writing rendered file throws IOError
        write_mock = open_mock().__enter__().write
        open_mock.reset_mock()
        write_mock.side_effect = IOError()
        Template_mock().render_unicode.return_value = "rendered_template"
        gandalf.main()
        open_mock.assert_called_once_with("rendered/outfile", "w", encoding="utf8")
        write_mock.assert_called_once_with("rendered_template")
        exit_mock.assert_called_once_with(0)
        reset_all_mocks()
        write_mock.side_effect = None


if __name__ == '__main__':
    unittest.main()
