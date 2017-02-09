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


    def test_dns(self):
        '''
            Test dns method.
        '''
        pass


    def test_rdns(self):
        '''
            Test dns method.
        '''
        pass


    def test_dhcp(self):
        '''
            Test dhcp method.
        '''
        pass


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


    def test_main(self):
        '''
            Test main function.
        '''
        pass


if __name__ == '__main__':
    unittest.main()
