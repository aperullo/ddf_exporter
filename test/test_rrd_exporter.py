import unittest
from unittest.mock import patch
import os
import rrd_exporter

class TestRrdExporter(unittest.TestCase):

    def setUp(self):
        # env vars for the test
        self.metric_prefix = 'test_case_'
        self.host = 'https://localhost:8993'

        print(os.getenv('METRIC_PREFIX'))

        # env vars previous to the test
        self.old_metric_prefix = os.getenv('METRIC_PREFIX')
        self.old_host = os.getenv('HOST_ADDRESS')

        # set the env vars to the test ones
        os.environ['METRIC_PREFIX'] = self.metric_prefix
        os.environ['HOST_ADDRESS'] = self.host


    def tearDown(self):
        print(os.getenv('METRIC_PREFIX'))

        # set the env vars to whatever they were before the tests,
        # if they were None, just unset them.
        if self.old_metric_prefix is None:
            # del is platform independent
            del os.environ['METRIC_PREFIX']
        else:
            os.environ['METRIC_PREFIX'] = self.old_metric_prefix

        if self.old_host is None:
            del os.environ['HOST_ADDRESS']
        else:
            os.environ['HOST_ADDRESS'] = self.old_host

    def mocked_requests_get(*args, **kwargs):

        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

        #todo: make the if's into a switch case
        if args[0] == 'https://localhost:8993/services/internal/metrics/':
            return MockResponse({'title': 'categoryQueries'}, 200)

        elif args[0] == 'https://localhost:8993/services/internal/metrics/testMetric.json?dateOffset=120':
            return MockResponse({'value': 0.0}, 200)

        elif args[0] == 'https://localhost:8993/services/internal/metrics/connectionError.json?dateOffset=120':
            return MockResponse({}, 403)

        return MockResponse(None, 404)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test__make_request(self, mock_get):
        exp = rrd_exporter.RRDCollector()

        #test_acquire_endpoints_request
        json_data = exp._make_request('', offset=None)
        self.assertEqual(json_data, {'title': 'categoryQueries'}, 200)

        #test successful request
        exp.metric_endpoints['test_metric'] = 'testMetric'
        json_data = exp._make_request('test_metric')
        self.assertEqual(json_data, {'value': 0.0}, 200)

        #test_site_not_found_request
        exp.metric_endpoints['not_found_metric'] = 'notFoundMetric'
        json_data = exp._make_request('not_found_metric')
        self.assertIsNone(json_data)

        #test_no_data_field_response
        exp.metric_endpoints['connection_error'] = 'connectionError'
        json_data = exp._make_request('connection_error')
        print(json_data)
        self.assertDictEqual(json_data,{})

    def test__json_to_metric_generator(self):

        #test empty dict
        gen = rrd_exporter._json_to_metric_generator({})
        self.assertRaises(StopIteration, next, gen)

        #test dict with no data attribute
        gen = rrd_exporter._json_to_metric_generator({'title': 'Empty'})
        self.assertRaises(StopIteration, next, gen)

        #test dict with 1 result
        gen = rrd_exporter._json_to_metric_generator({
                'title': '1data',
                'data': [{'value': 0.0, 'timestamp': 'Jan 15 2019 12:07:00'}]})

        self.assertDictEqual(next(gen), {'value': 0.0, 'timestamp': 'Jan 15 2019 12:07:00'})

        self.assertRaises(StopIteration, next, gen)

        #test dict with multiple results




