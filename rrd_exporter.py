

from prometheus_client import start_http_server
from prometheus_client.core import InfoMetricFamily, HistogramMetricFamily, CounterMetricFamily, GaugeMetricFamily, SummaryMetricFamily, REGISTRY

import json, requests, sys, time, os, signal, re




class RRDCollector:

    # The collect method is used whenever a scrape request from prometheus activates this script.
    def collect(self):

        # TODO: get host name for labels
        metric_prefix = 'rrd_'
        host = 'https://10.103.2.33:8993'
        metric_api_location = 'services/internal/metrics'
        file_ext = '.json'

        # TODO: set headers
        # TODO: Env variable for system name


        # Offset is from the present, how many seconds into the past to fetch for that metric.
        # TODO: if offset is less than 120, then there may be no record, as the server may still be collecting that info.
        def _make_request(metric_name: str, offset=120):
            """
            Sends a get request based on a specified metric, and then returns the json.

            :param metric_name: The name of the metric, which will be used to lookup the corresponding endpoint
            :param offset: From the present, how many seconds into the past to fetch data for that metric
            :return: The dict/json representing the response
            """
            # TODO: find safer way to build url
            query_url = ''

            # If no offset, then we only want the base url.
            if offset is not None:
                query_url = ''.join([metrics_endpoints.get(metric_name),
                                     file_ext,
                                     '?dateOffset=',
                                     str(offset)])

            query_url = '/'.join([host, metric_api_location, query_url])

            download = None

            try:
                download = requests.get(query_url, verify=False)  # TODO make SSL cert valid, this is an insecure hack
            except ConnectionRefusedError:
                pass  # TODO: what to do here

            metric_json = download.json()

            return metric_json

        def fetch_available_endpoints():
            """
            Query the metrics endpoint to get available metrics, then process the result into a snake_case: camelCase
            dictionary.

            :return: a dict representing the snake_case: camelCase available endpoints
            """

            endpoints = list(_make_request('', offset=None).keys())

            available_endpoints = {}
            for endpoint in endpoints:
                available_endpoints[_camel_to_snake_case(endpoint)] = endpoint

            return available_endpoints

        def populate_and_fetch_metrics(available_endpoints, prefix, labels=None):
            """
            Query each available endpoint, retrieve it's value/values at that time, and store it into a results dictionary.

            :param available_endpoints: dictionary of snake_case: camelCase strings representing metric endpoints
            :param prefix: the prefix to be prepended to all metrics generated by this exporter
            :param labels: an optional set of tags for to include on the metrics
            :return: a dictionary of metrics with their corresponding values as retrieved from the endpoint
            """
            metric_results = {}

            if labels is None:
                labels = {}

            # for every available endpoint
            for metric_name in available_endpoints.keys():

                # Create an empty metric for that endpoint to hold its results
                metric_results[metric_name] = GaugeMetricFamily(prefix + metric_name, metric_name)

                # Call to that endpoint and add all of its datapoints to the results.
                for data_point in _json_to_metric_generator(_make_request(metric_name)):
                    #TODO: what should labels be?
                    #TODO: TImestamps are decided when prometheus receives them because the ones from RRD are considered too old
                    metric_results[metric_name].add_metric(labels=labels, value=data_point['value'])
                    # timestamp=datetime.datetime.strptime(data_point['timestamp'],
                    #                             '%b %d %Y %X').timetz())

            return metric_results

        metrics_endpoints = fetch_available_endpoints()

        metric_results = populate_and_fetch_metrics(metrics_endpoints, metric_prefix)

        print(metric_results['catalog_queries'])

        for metric_name in metrics_endpoints.keys():
            yield metric_results[metric_name]


def _json_to_metric_generator(json_response: dict):
    """
    :rtype: dict
    """
    # assembled_metric = Metric()

    # see if there are any data tags inside the response
    data = json_response.get('data')
    # print(data)
    if (data == None):
        yield

    for data_point in data:
        yield data_point


def _camel_to_snake_case(string: str):
    """
    :rtype: str
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

if __name__ == '__main__':
    # Ensure we have something to export
    #TODO: binding port
    #start_http_server(int(os.getenv('BIND_PORT')))
    REGISTRY.register(RRDCollector())

    signal.signal(signal.SIGTERM, sigterm_handler)
    while True:
        time.sleep(1)