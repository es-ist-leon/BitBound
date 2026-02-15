"""
HTTP Client and Server for BitBound.

Provides simple HTTP client for API calls and a minimal HTTP server
for device dashboards.
"""

import json
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class HTTPResponse:
    """HTTP response object."""
    status_code: int = 200
    headers: Dict[str, str] = None
    body: bytes = b""
    text: str = ""
    json_data: Any = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.body and not self.text:
            try:
                self.text = self.body.decode("utf-8")
            except Exception:
                pass
        if self.text and self.json_data is None:
            try:
                self.json_data = json.loads(self.text)
            except (json.JSONDecodeError, ValueError):
                pass

    def json(self) -> Any:
        """Parse response body as JSON."""
        if self.json_data is not None:
            return self.json_data
        return json.loads(self.text)


class HTTPClient:
    """
    Simple HTTP client for MicroPython and desktop.

    Example:
        from bitbound.network import HTTPClient

        http = HTTPClient()
        response = http.get("http://api.example.com/data")
        print(response.json())

        http.post("http://api.example.com/data",
                  json={"temperature": 23.5})
    """

    def __init__(self, timeout: int = 10, headers: Optional[Dict[str, str]] = None):
        self._timeout = timeout
        self._default_headers = headers or {}
        self._simulation = True
        self._sim_responses: Dict[str, HTTPResponse] = {}

        self._detect_backend()

    def _detect_backend(self) -> None:
        """Detect available HTTP backend."""
        try:
            import urequests
            self._backend = "urequests"
            self._simulation = False
        except ImportError:
            try:
                import requests
                self._backend = "requests"
                self._simulation = False
            except ImportError:
                try:
                    import urllib.request
                    self._backend = "urllib"
                    self._simulation = False
                except ImportError:
                    self._backend = "simulation"
                    self._simulation = True

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[bytes] = None,
        json_data: Optional[Any] = None,
        timeout: Optional[int] = None,
    ) -> HTTPResponse:
        """
        Send an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            headers: Request headers
            data: Request body
            json_data: JSON request body (auto-serialized)
            timeout: Request timeout

        Returns:
            HTTPResponse object
        """
        all_headers = {**self._default_headers, **(headers or {})}
        timeout = timeout or self._timeout

        if json_data is not None:
            data = json.dumps(json_data).encode("utf-8")
            all_headers.setdefault("Content-Type", "application/json")

        if self._simulation:
            return self._sim_request(method, url, all_headers, data)

        try:
            if self._backend == "urequests":
                return self._urequests_request(method, url, all_headers, data)
            elif self._backend == "requests":
                return self._requests_request(method, url, all_headers, data, timeout)
            else:
                return self._urllib_request(method, url, all_headers, data, timeout)
        except Exception as e:
            return HTTPResponse(status_code=0, text=str(e))

    def _urequests_request(self, method, url, headers, data) -> HTTPResponse:
        """MicroPython urequests backend."""
        import urequests
        resp = urequests.request(method, url, headers=headers, data=data)
        result = HTTPResponse(
            status_code=resp.status_code,
            body=resp.content,
            text=resp.text,
        )
        resp.close()
        return result

    def _requests_request(self, method, url, headers, data, timeout) -> HTTPResponse:
        """Python requests backend."""
        import requests
        resp = requests.request(method, url, headers=headers, data=data, timeout=timeout)
        return HTTPResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            body=resp.content,
            text=resp.text,
        )

    def _urllib_request(self, method, url, headers, data, timeout) -> HTTPResponse:
        """Python urllib backend."""
        import urllib.request
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            body = resp.read()
            return HTTPResponse(
                status_code=resp.status,
                headers=dict(resp.headers),
                body=body,
            )
        except urllib.error.HTTPError as e:
            return HTTPResponse(status_code=e.code, body=e.read())

    def _sim_request(self, method, url, headers, data) -> HTTPResponse:
        """Simulation backend."""
        key = f"{method}:{url}"
        if key in self._sim_responses:
            return self._sim_responses[key]
        return HTTPResponse(status_code=200, text='{"status":"ok","simulated":true}')

    def set_sim_response(self, method: str, url: str, response: HTTPResponse) -> None:
        """Set a simulated response for testing."""
        self._sim_responses[f"{method}:{url}"] = response

    def get(self, url: str, **kwargs) -> HTTPResponse:
        """Send a GET request."""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> HTTPResponse:
        """Send a POST request."""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> HTTPResponse:
        """Send a PUT request."""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> HTTPResponse:
        """Send a DELETE request."""
        return self.request("DELETE", url, **kwargs)

    def __repr__(self) -> str:
        return f"<HTTPClient backend={self._backend}>"


class HTTPServer:
    """
    Minimal HTTP server for device dashboards and REST APIs.

    Example:
        from bitbound.network import HTTPServer

        server = HTTPServer(port=80)

        @server.route("/api/temperature")
        def get_temp(request):
            return {"temperature": 23.5}

        server.start()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 80):
        self._host = host
        self._port = port
        self._routes: Dict[str, Dict[str, Callable]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._simulation = True
        self._socket = None

        self._detect_backend()

    def _detect_backend(self) -> None:
        """Detect available socket backend."""
        try:
            import usocket
            self._simulation = False
        except ImportError:
            try:
                import socket
                self._simulation = False
            except ImportError:
                self._simulation = True

    def route(self, path: str, methods: List[str] = None):
        """
        Decorator to register a route handler.

        Args:
            path: URL path
            methods: Allowed HTTP methods (default: ["GET"])
        """
        methods = methods or ["GET"]

        def decorator(func):
            for method in methods:
                key = f"{method.upper()}:{path}"
                self._routes[key] = func
            return func

        return decorator

    def add_route(self, path: str, handler: Callable, methods: List[str] = None) -> None:
        """Register a route handler programmatically."""
        methods = methods or ["GET"]
        for method in methods:
            self._routes[f"{method.upper()}:{path}"] = handler

    def start(self, background: bool = True) -> None:
        """
        Start the HTTP server.

        Args:
            background: Run in background thread
        """
        self._running = True

        if self._simulation:
            print(f"[SIM] HTTP Server on {self._host}:{self._port}")
            return

        if background:
            self._thread = threading.Thread(target=self._serve, daemon=True)
            self._thread.start()
        else:
            self._serve()

    def stop(self) -> None:
        """Stop the HTTP server."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2)

    def _serve(self) -> None:
        """Main server loop."""
        try:
            try:
                import usocket as socket_mod
            except ImportError:
                import socket as socket_mod

            self._socket = socket_mod.socket()
            self._socket.setsockopt(socket_mod.SOL_SOCKET, socket_mod.SO_REUSEADDR, 1)
            self._socket.bind((self._host, self._port))
            self._socket.listen(5)
            self._socket.settimeout(1.0)

            while self._running:
                try:
                    client, addr = self._socket.accept()
                    self._handle_client(client)
                except OSError:
                    continue
                except Exception as e:
                    print(f"Server error: {e}")

        except Exception as e:
            print(f"Server fatal error: {e}")
        finally:
            if self._socket:
                self._socket.close()

    def _handle_client(self, client) -> None:
        """Handle an incoming client connection."""
        try:
            request_data = client.recv(4096).decode("utf-8")
            if not request_data:
                return

            lines = request_data.split("\r\n")
            request_line = lines[0].split(" ")
            method = request_line[0]
            path = request_line[1].split("?")[0] if len(request_line) > 1 else "/"

            key = f"{method}:{path}"
            handler = self._routes.get(key)

            if handler:
                result = handler({"method": method, "path": path, "raw": request_data})
                if isinstance(result, dict):
                    body = json.dumps(result)
                    content_type = "application/json"
                elif isinstance(result, str):
                    body = result
                    content_type = "text/html"
                else:
                    body = str(result)
                    content_type = "text/plain"

                response = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {content_type}\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Connection: close\r\n\r\n{body}"
                )
            else:
                response = "HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\nConnection: close\r\n\r\nNot Found"

            client.send(response.encode("utf-8"))
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            client.close()

    @property
    def is_running(self) -> bool:
        return self._running

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return f"<HTTPServer {self._host}:{self._port} [{status}]>"
