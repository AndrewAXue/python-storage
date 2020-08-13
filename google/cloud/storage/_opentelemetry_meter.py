# Copyright 2014 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manages OpenTelemetry metrics creation and handling"""

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import Counter, MeterProvider
    from opentelemetry.exporter.cloud_monitoring import (
        CloudMonitoringMetricsExporter,
    )

    HAS_OPENTELEMETRY_INSTALLED = True
except ImportError:
    HAS_OPENTELEMETRY_INSTALLED = False

FUNCTION_NAME_KEY = 'instrumented_function_name'

if HAS_OPENTELEMETRY_INSTALLED:
    meter = metrics.get_meter(__name__)
    metrics.set_meter_provider(MeterProvider(stateful=False))
    metrics.get_meter_provider().start_pipeline(
        meter, CloudMonitoringMetricsExporter(), 15
    )
    requests_counter = meter.create_metric(
        name="GCS_request_counter",
        description="number of requests",
        unit="1",
        value_type=int,
        metric_type=Counter,
    )

    def telemetry_wrapped_api_request(api_request, *args, **kwargs):
        instrumented_labels = {}
        if FUNCTION_NAME_KEY in kwargs:
            instrumented_labels['function_name'] = kwargs[FUNCTION_NAME_KEY]
            kwargs.pop(FUNCTION_NAME_KEY)
        elif 'path' in kwargs:
            instrumented_labels['function_name'] = '{} {}'.format(kwargs['method'], kwargs['path'])

        print(instrumented_labels)
        requests_counter.add(1, instrumented_labels)
        return api_request(*args, **kwargs)
else:
    def telemetry_wrapped_api_request(api_request, *args, **kwargs):
        if FUNCTION_NAME_KEY in kwargs:
            kwargs.pop(FUNCTION_NAME_KEY)
        return api_request(*args, **kwargs)
