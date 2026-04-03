from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import time
import unittest

from drone_telemetry.contracts import TelemetryEnvelope
from drone_telemetry.transport import AsyncTelemetryPublisher, TelemetryApiClient


class _CaptureHandler(BaseHTTPRequestHandler):
    received: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(content_length)
        self.__class__.received.append(json.loads(payload.decode("utf-8")))
        self.send_response(202)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A003
        del format, args


class TestTelemetryTransport(unittest.TestCase):
    def test_client_posts_envelope_to_api(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), _CaptureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        _CaptureHandler.received.clear()

        client = TelemetryApiClient(f"http://127.0.0.1:{server.server_port}", timeout_s=1.0)
        publisher = AsyncTelemetryPublisher(client)
        try:
            publisher.submit(
                TelemetryEnvelope(
                    run_id="run-1",
                    source="telemetry_bridge",
                    kind="vehicle_state",
                    topic="/drone/vehicle_state",
                    stamp_ns=123,
                    payload={"connected": True},
                )
            )
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not _CaptureHandler.received:
                time.sleep(0.05)
        finally:
            publisher.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        self.assertEqual(len(_CaptureHandler.received), 1)
        self.assertEqual(_CaptureHandler.received[0]["kind"], "vehicle_state")

    def test_publisher_records_backend_failure_without_crashing(self) -> None:
        client = TelemetryApiClient("http://127.0.0.1:9", timeout_s=0.2)
        publisher = AsyncTelemetryPublisher(client)
        try:
            publisher.submit(
                TelemetryEnvelope(
                    run_id="run-backend-loss",
                    source="telemetry_bridge",
                    kind="mission_status",
                    topic="/drone/mission_status",
                    stamp_ns=456,
                    payload={"phase": "patrol"},
                )
            )
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not publisher.last_error:
                time.sleep(0.05)
        finally:
            publisher.close()

        self.assertIn("failed to reach telemetry api", publisher.last_error)


if __name__ == "__main__":
    unittest.main()
