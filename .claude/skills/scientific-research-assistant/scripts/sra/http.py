"""HTTP client shared by every source: throttling, retries, caching, typed errors."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "scientific-research-assistant/1.0 (Claude Code skill; stdlib urllib)"
RETRY_STATUS = {429, 500, 502, 503, 504}

# Minimum seconds between requests per host, following each provider's guidance.
MIN_INTERVAL = {
    "export.arxiv.org": 3.0,  # arXiv asks for one request every 3 seconds
    "arxiv.org": 3.0,  # e-print sources and HTML full text: same courtesy as the API
    "api.semanticscholar.org": 1.1,
    "eutils.ncbi.nlm.nih.gov": 0.35,  # 3 req/s without an API key
    "api.github.com": 0.75,
    "api.crossref.org": 0.2,
    "api.openalex.org": 0.15,
    "huggingface.co": 0.25,
    "datasets-server.huggingface.co": 0.25,
    "zenodo.org": 1.0,
    "doi.org": 0.2,
}


class SourceError(Exception):
    """A request to an external source failed in a way the caller should report.

    kind is one of: rate_limited, auth, not_found, network, http, parse, too_large.
    """

    def __init__(self, source: str, kind: str, message: str, status: int | None = None):
        super().__init__(f"[{source}] {kind}: {message}")
        self.source, self.kind, self.message, self.status = source, kind, message, status

    def to_dict(self) -> dict:
        return {"source": self.source, "kind": self.kind, "message": self.message, "status": self.status}


def default_cache_dir() -> str | None:
    env = os.environ.get("SRA_CACHE_DIR")
    if env is not None:
        return None if env.strip().lower() in ("", "off", "none", "0") else env
    return os.path.join(tempfile.gettempdir(), "sra_cache")


def _server_message(exc) -> str:
    """The provider's own short explanation of an error, when it sent one."""
    try:
        data = json.loads(exc.read().decode("utf-8", "replace"))
        text = data.get("message") or data.get("error") or ""
    except Exception:  # noqa: BLE001 - any unreadable body just means no detail
        return ""
    return str(text)[:240]


def _accepts_size(resp) -> bool:
    """True when resp.read takes a size argument (real responses do; some test fakes do not)."""
    try:
        import inspect
        return len(inspect.signature(resp.read).parameters) > 0
    except (TypeError, ValueError):
        return True


class HttpClient:
    def __init__(self, timeout: float = 30, max_retries: int = 3, backoff: float = 2.0,
                 max_wait: float = 20.0, cache_dir: str | None = "default", cache_ttl: float = 86400,
                 opener=None, sleep=time.sleep, clock=time.monotonic):
        self.timeout, self.max_retries, self.backoff, self.max_wait = timeout, max_retries, backoff, max_wait
        self.cache_dir = default_cache_dir() if cache_dir == "default" else cache_dir
        self.cache_ttl = cache_ttl
        self._open = opener or urllib.request.urlopen
        self._sleep, self._clock = sleep, clock
        self._last: dict[str, float] = {}
        self.request_count = 0  # network requests actually sent (including retries)
        self.call_count = 0  # get() calls, served from cache or network
        self.offline = False  # replay mode: a cache miss fails instead of reaching the network

    # -- cache ---------------------------------------------------------
    def _cache_path(self, full_url: str) -> str | None:
        if not self.cache_dir:
            return None
        return os.path.join(self.cache_dir, hashlib.sha256(full_url.encode()).hexdigest() + ".json")

    def _cache_get(self, full_url: str) -> str | None:
        path = self._cache_path(full_url)
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                entry = json.load(fh)
            if time.time() - entry["ts"] <= self.cache_ttl:
                return entry["body"]
        except (OSError, ValueError, KeyError):
            pass
        return None

    def _cache_put(self, full_url: str, body: str) -> None:
        path = self._cache_path(full_url)
        if not path:
            return
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"ts": time.time(), "url": full_url, "body": body}, fh)
        except OSError:
            pass  # caching is best-effort

    # -- request -------------------------------------------------------
    def _throttle(self, host: str) -> None:
        wait = MIN_INTERVAL.get(host, 0.0) - (self._clock() - self._last.get(host, -1e9))
        if wait > 0:
            self._sleep(wait)
        self._last[host] = self._clock()

    def get(self, url: str, params: dict | None = None, headers: dict | None = None, source: str = "",
            parse: str = "json", cache: bool = True, retries: int | None = None):
        """GET url. parse is 'json' or 'text'. Raises SourceError on failure."""
        full_url = url
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            full_url = f"{url}{'&' if '?' in url else '?'}{query}"
        host = urllib.parse.urlsplit(full_url).netloc
        source = source or host

        self.call_count += 1
        body = self._cache_get(full_url) if cache else None
        if body is None and self.offline:
            raise SourceError(source, "not_found", "not in the replay snapshot (offline mode)")
        if body is None:
            body = self._fetch(full_url, host, headers or {}, source,
                               self.max_retries if retries is None else retries)
            if cache:
                self._cache_put(full_url, body)
        if parse == "text":
            return body
        try:
            return json.loads(body)
        except ValueError as exc:
            raise SourceError(source, "parse", f"response was not valid JSON: {exc}") from exc

    def get_bytes(self, url: str, source: str = "", max_bytes: int = 25_000_000,
                  headers: dict | None = None) -> bytes:
        """GET a binary resource (not cached). Refuses bodies larger than max_bytes."""
        host = urllib.parse.urlsplit(url).netloc
        body = self._fetch(url, host, {"Accept": "*/*", **(headers or {})}, source or host, self.max_retries,
                           raw=True, max_bytes=max_bytes)
        return body

    def cache_text(self, key: str, value: str | None = None) -> str | None:
        """Store (value given) or look up (no value) derived text under a synthetic cache key."""
        if value is None:
            return self._cache_get(key)
        self._cache_put(key, value)
        return value

    def _fetch(self, full_url: str, host: str, headers: dict, source: str, retries: int,
               raw: bool = False, max_bytes: int | None = None):
        req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        contact = os.environ.get("SRA_CONTACT_EMAIL")
        if contact:
            req_headers["User-Agent"] = f"{USER_AGENT} mailto:{contact}"
        req_headers.update(headers)

        attempt = 0
        while True:
            self._throttle(host)
            self.request_count += 1
            try:
                req = urllib.request.Request(full_url, headers=req_headers)
                with self._open(req, timeout=self.timeout) as resp:
                    if max_bytes is not None:
                        data = resp.read(max_bytes + 1) if _accepts_size(resp) else resp.read()
                        if len(data) > max_bytes:
                            raise SourceError(source, "too_large", f"response exceeds {max_bytes} bytes; "
                                              "not downloaded")
                    else:
                        data = resp.read()
                    return data if raw else data.decode("utf-8", "replace")
            except urllib.error.HTTPError as exc:
                status, hdrs = exc.code, exc.headers or {}
                if status in (403, 429) and str(hdrs.get("X-RateLimit-Remaining", "")) == "0":
                    detail = _server_message(exc) or "set the source's API key to raise the limit"
                    raise SourceError(source, "rate_limited", f"quota exhausted (X-RateLimit-Reset="
                                      f"{hdrs.get('X-RateLimit-Reset', '?')}). {detail}", status) from exc
                if status in RETRY_STATUS and attempt < retries:
                    wait = self._retry_wait(hdrs.get("Retry-After"), attempt)
                    if wait is not None:
                        self._sleep(wait)
                        attempt += 1
                        continue
                if status == 429:
                    raise SourceError(source, "rate_limited", "HTTP 429 after retries", status) from exc
                if status in (401, 403):
                    raise SourceError(source, "auth", f"HTTP {status}: access denied or key required", status) from exc
                if status == 404:
                    raise SourceError(source, "not_found", "HTTP 404", status) from exc
                raise SourceError(source, "http", f"HTTP {status}", status) from exc
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
                if attempt < retries:
                    self._sleep(min(self.backoff * (2 ** attempt), self.max_wait))
                    attempt += 1
                    continue
                raise SourceError(source, "network", str(getattr(exc, "reason", exc))) from exc

    def probe(self, url: str) -> dict:
        """Check that a URL answers, without downloading its body."""
        host = urllib.parse.urlsplit(url).netloc
        result = {"url": url, "reachable": False, "status": None}
        for method, extra in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
            self._throttle(host)
            self.request_count += 1
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **extra}, method=method)
                with self._open(req, timeout=self.timeout) as resp:
                    headers = getattr(resp, "headers", None) or {}
                    result.update(reachable=True, status=getattr(resp, "status", 200),
                                  content_type=headers.get("Content-Type"),
                                  content_length=headers.get("Content-Length") if method == "HEAD" else None)
                    return result
            except urllib.error.HTTPError as exc:
                result["status"] = exc.code
                if method == "HEAD" and exc.code in (403, 405, 501):
                    continue  # some hosts reject HEAD but serve GET
                return result
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
                result["error"] = str(getattr(exc, "reason", exc))
                return result
        return result

    def _retry_wait(self, retry_after, attempt: int) -> float | None:
        """Seconds to wait before retrying, or None when the server asks for too long."""
        if retry_after:
            try:
                wait = float(retry_after)
                return wait if wait <= self.max_wait else None
            except ValueError:
                pass
        return min(self.backoff * (2 ** attempt), self.max_wait)
