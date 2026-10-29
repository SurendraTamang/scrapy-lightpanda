"""Compare CPU time + peak RAM of raw headless browsers loading real sites (CPU time = energy proxy).

Needs: pip install camoufox psutil && camoufox fetch && playwright install chromium-headless-shell
"""
import os, shutil, subprocess, threading, time, psutil
from playwright.sync_api import sync_playwright
from camoufox.sync_api import NewBrowser

SITES = ["https://news.ycombinator.com", "https://en.wikipedia.org/wiki/Web_browser", "https://www.bbc.com/news"]
RUNS = 5
LP = shutil.which("lightpanda") or "lightpanda"


class Sampler(threading.Thread):
    """Sum CPU + RSS of every descendant of this python process, except the Playwright node driver."""
    def __init__(self):
        super().__init__(daemon=True)
        self.cpu, self.peak_rss, self.stop = {}, 0, False

    def run(self):
        me = psutil.Process()
        while not self.stop:
            rss = 0
            for p in me.children(recursive=True):
                try:
                    if p.name() == "node":
                        continue
                    t = p.cpu_times()
                    self.cpu[p.pid] = t.user + t.system
                    rss += p.memory_info().rss
                except psutil.Error:
                    pass
            self.peak_rss = max(self.peak_rss, rss)
            time.sleep(0.05)


def load_all(browser, url):
    ctx = browser.new_context()
    page = ctx.new_page()
    ok, chars = 0, 0
    for _ in range(RUNS):
        try:
            page.goto(url, wait_until="load", timeout=60000)
            chars = len(page.inner_text("body"))
            ok += chars > 200  # content check, not just "no error"
        except Exception as e:
            print("   err:", str(e).splitlines()[0][:100])
    ctx.close()
    return ok, chars


def chromium(pw):
    return pw.chromium.launch(headless=True)


def lightpanda(pw):
    env = {**os.environ, "LIGHTPANDA_DISABLE_TELEMETRY": "true"}
    proc = subprocess.Popen([LP, "serve", "--host", "127.0.0.1", "--port", "9333"],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    b = pw.chromium.connect_over_cdp("http://127.0.0.1:9333")
    b._lp = proc
    return b


def camoufox(_pw):
    return NewBrowser(_pw, headless=True)


def close(b):
    b.close()
    if hasattr(b, "_lp"):
        b._lp.terminate(); b._lp.wait()


def measure(name, launch, pw, url):
    s = Sampler(); s.start()
    t0 = time.time()
    b = launch(pw)
    ok, chars = load_all(b, url)
    close(b)
    wall = time.time() - t0
    s.stop = True; s.join()
    return dict(browser=name, site=url.split("//")[1], ok=f"{ok}/{RUNS}", chars=chars,
                cpu_s=round(sum(s.cpu.values()), 2), peak_mb=round(s.peak_rss / 2**20), wall_s=round(wall, 1))


if __name__ == "__main__":
    browsers = [("lightpanda", lightpanda), ("chromium-headless", chromium), ("camoufox", camoufox)]
    rows = []
    with sync_playwright() as pw:
        for name, fn in browsers:  # warm-up: disk cache, first-launch installs
            close(fn(pw))
        for url in SITES:
            for name, fn in browsers:
                r = measure(name, fn, pw, url)
                print(r, flush=True)
                rows.append(r)
