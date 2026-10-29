"""scrapy-playwright browser provider that runs the Lightpanda headless browser."""

import asyncio
import os
import shutil
import socket

from scrapy.exceptions import NotConfigured, NotSupported
from scrapy_playwright.provider import PlaywrightBrowserProvider

__all__ = ["LightpandaBrowserProvider"]
__version__ = "0.1.0"

HOST = "127.0.0.1"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


class LightpandaBrowserProvider(PlaywrightBrowserProvider):
    """Start ``lightpanda serve`` on a free local port and connect to it over CDP.

    Reads ``PLAYWRIGHT_LAUNCH_OPTIONS``: ``executable_path``, ``args`` (extra
    ``lightpanda serve`` flags), ``env`` and ``timeout`` (ms to wait for startup).
    """

    def __init__(self, config) -> None:
        super().__init__(config)
        opts = dict(config.launch_options)
        self.executable = opts.pop("executable_path", None) or shutil.which("lightpanda")
        self.args = [str(a) for a in opts.pop("args", [])]
        self.timeout = opts.pop("timeout", 10_000) / 1000
        # Lightpanda sends usage telemetry by default; opt out unless the user says otherwise.
        self.env = {"LIGHTPANDA_DISABLE_TELEMETRY": "true", **os.environ, **opts.pop("env", {})}
        if opts:
            raise NotConfigured(f"PLAYWRIGHT_LAUNCH_OPTIONS not supported by Lightpanda: {sorted(opts)}")
        if not self.executable:
            raise NotConfigured(
                "lightpanda binary not found on PATH; set PLAYWRIGHT_LAUNCH_OPTIONS['executable_path']"
            )
        # A Lightpanda CDP connection holds one context with one page; more fail with TargetAlreadyLoaded.
        config.max_pages_per_context = 1
        self.process = None
        self.port = None

    async def launch_browser(self):
        if self.playwright is None:
            raise RuntimeError("start() must be awaited before launch_browser()")
        if self.process is None or self.process.returncode is not None:  # first launch or crashed
            self.port = _free_port()
            self.process = await asyncio.create_subprocess_exec(
                self.executable, "serve", "--host", HOST, "--port", str(self.port), *self.args,
                env=self.env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await self._wait_until_listening()
        return await self.playwright.chromium.connect_over_cdp(
            f"http://{HOST}:{self.port}", **self.config.cdp_kwargs
        )

    async def _wait_until_listening(self) -> None:
        deadline = asyncio.get_running_loop().time() + self.timeout
        while True:
            if self.process.returncode is not None:
                raise RuntimeError(f"lightpanda exited with code {self.process.returncode}")
            try:
                _, writer = await asyncio.open_connection(HOST, self.port)
                writer.close()
                return
            except OSError:
                if asyncio.get_running_loop().time() > deadline:
                    raise TimeoutError(f"lightpanda did not listen on port {self.port} in {self.timeout}s")
                await asyncio.sleep(0.05)

    async def launch_persistent_context(self, context_kwargs: dict):
        raise NotSupported("Lightpanda does not support persistent contexts (user_data_dir)")

    async def close(self) -> None:
        await super().close()
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), 5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
