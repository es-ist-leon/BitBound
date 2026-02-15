"""Tests for HTTP Client and Server."""

import pytest
from bitbound.network.http import HTTPClient, HTTPServer, HTTPResponse


class TestHTTPClient:
    def _sim_client(self):
        """Create an HTTPClient forced into simulation mode."""
        http = HTTPClient()
        http._simulation = True
        http._backend = "simulation"
        return http

    def test_create_client(self):
        http = HTTPClient()
        assert http is not None

    def test_get_simulation(self):
        http = self._sim_client()
        response = http.get("http://example.com/api")
        assert response.status_code == 200
        assert response.text != ""

    def test_post_simulation(self):
        http = self._sim_client()
        response = http.post("http://example.com/api", json_data={"temp": 23.5})
        assert response.status_code == 200

    def test_set_sim_response(self):
        http = self._sim_client()
        http.set_sim_response("GET", "http://test.com/data",
                              HTTPResponse(status_code=201, text='{"value": 42}'))
        response = http.get("http://test.com/data")
        assert response.status_code == 201
        assert response.json()["value"] == 42

    def test_response_json(self):
        resp = HTTPResponse(text='{"key": "value"}')
        assert resp.json()["key"] == "value"

    def test_response_from_bytes(self):
        resp = HTTPResponse(body=b'{"test": true}')
        assert resp.text == '{"test": true}'
        assert resp.json()["test"] is True

    def test_default_headers(self):
        http = HTTPClient(headers={"Authorization": "Bearer token"})
        assert http._default_headers["Authorization"] == "Bearer token"

    def test_put_and_delete(self):
        http = self._sim_client()
        assert http.put("http://example.com/api").status_code == 200
        assert http.delete("http://example.com/api").status_code == 200

    def test_repr(self):
        http = HTTPClient()
        assert "HTTPClient" in repr(http)


class TestHTTPServer:
    def test_create_server(self):
        server = HTTPServer(port=8080)
        assert not server.is_running

    def test_route_decorator(self):
        server = HTTPServer()

        @server.route("/test")
        def handler(request):
            return {"status": "ok"}

        assert "GET:/test" in server._routes

    def test_add_route(self):
        server = HTTPServer()
        server.add_route("/api/data", lambda r: {"data": 42}, methods=["GET", "POST"])
        assert "GET:/api/data" in server._routes
        assert "POST:/api/data" in server._routes

    def test_start_stop_simulation(self):
        server = HTTPServer()
        server.start()
        assert server.is_running
        server.stop()
        assert not server.is_running

    def test_repr(self):
        server = HTTPServer(host="0.0.0.0", port=80)
        assert "HTTPServer" in repr(server)
