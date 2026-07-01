"""Fetch a URL and output clean text (or markdown via Jina Reader).

Handles arxiv papers, GitHub repos, HTML articles, and PDFs.
Generic HTML is fetched through Jina Reader (r.jina.ai) first,
with a local BeautifulSoup fallback if Jina is unavailable.
"""

import re
import zlib
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import click
from bs4 import BeautifulSoup

from bonsai import get_url, resolve_ref


class FetchError(Exception):
    """Raised when source text cannot be extracted."""

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

STRIP_TAGS = {
    "script", "style", "nav", "footer", "header", "aside",
    "form", "button", "svg", "iframe", "noscript",
}

ARXIV_SELECTORS = ["article", ".ltx_page_content", "main", "body"]

ARTICLE_SELECTORS = [
    "article",
    '[role="main"]',
    "main",
    ".post-content",
    ".article-body",
    ".entry-content",
    "#content",
    ".markdown-body",
    "body",
]

JINA_PREFIX = "https://r.jina.ai/"


# ---------------------------------------------------------------------------
# URL detection and rewriting
# ---------------------------------------------------------------------------

def _classify_url(url: str) -> str:
    """Return one of: arxiv, github, pdf, html."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "arxiv.org" in host:
        return "arxiv"
    if "github.com" in host:
        return "github"
    if parsed.path.lower().endswith(".pdf"):
        return "pdf"
    return "html"


def _arxiv_id(url: str) -> str | None:
    """Extract the arXiv identifier from an abs/html/pdf URL."""
    parsed = urlparse(url)
    match = re.search(r"/(abs|pdf|html)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?$", parsed.path)
    if match:
        return match.group(2)
    return None


def _arxiv_to_html(url: str) -> str:
    """Rewrite an arxiv URL to its HTML rendering."""
    paper_id = _arxiv_id(url)
    if paper_id:
        return f"https://arxiv.org/html/{paper_id}"
    return url


def _arxiv_to_abs(url: str) -> str:
    paper_id = _arxiv_id(url)
    if paper_id:
        return f"https://arxiv.org/abs/{paper_id}"
    return url


def _arxiv_to_pdf(url: str) -> str:
    paper_id = _arxiv_id(url)
    if paper_id:
        return f"https://arxiv.org/pdf/{paper_id}"
    return url


def _github_to_raw_readme(url: str) -> str | None:
    """Given a GitHub repo URL, return the raw README URL."""
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        return None

    user, repo = parts[0], parts[1]
    branch = "main"
    subdir = ""
    if len(parts) >= 4 and parts[2] == "tree":
        branch = parts[3]
        subdir = "/".join(parts[4:])

    branches = [branch]
    if branch == "main":
        branches.append("master")

    for candidate_branch in branches:
        base = f"https://raw.githubusercontent.com/{user}/{repo}/{candidate_branch}"
        if subdir:
            base += f"/{subdir}"

        for name in ["README.md", "readme.md", "README"]:
            test_url = f"{base}/{name}"
            try:
                req = Request(test_url, headers={"User-Agent": USER_AGENT})
                urlopen(req, timeout=10)
                return test_url
            except Exception:
                continue
    return None


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def _fetch_jina(url: str) -> str:
    """Fetch via Jina Reader and return extracted markdown.

    Raises FetchError on network problems, non-200 responses, or when
    the target page itself returned an error (Jina embeds a Warning line).
    """
    jina_url = url if url.startswith(JINA_PREFIX) else JINA_PREFIX + url
    req = Request(jina_url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/plain",
    })
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    # Jina returns JSON on errors (blocked domains, rate limits).
    if body.lstrip().startswith("{"):
        raise FetchError(f"jina returned error response for {url}")

    # Check for upstream errors (target returned 4xx/5xx).
    if re.search(r"^Warning:.*returned error", body, re.MULTILINE):
        raise FetchError(f"jina: target URL returned an error for {url}")

    # Strip the Title/URL Source/Markdown Content header.
    marker = "Markdown Content:"
    idx = body.find(marker)
    if idx != -1:
        body = body[idx + len(marker):]

    text = body.strip()
    if not text:
        raise FetchError(f"jina returned empty content for {url}")
    return text


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _extract_html(html_bytes: bytes, selectors: list[str]) -> str:
    """Parse HTML bytes and extract text from the first matching selector."""
    soup = BeautifulSoup(html_bytes, "lxml")
    for tag_name in STRIP_TAGS:
        for el in soup.find_all(tag_name):
            el.decompose()

    container = None
    for selector in selectors:
        container = soup.select_one(selector)
        if container:
            break
    if container is None:
        container = soup

    text = container.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf_basic(pdf_bytes: bytes) -> str:
    """Best-effort PDF text extraction using only stdlib."""
    text_parts: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.+?)\r?\nendstream", pdf_bytes, re.DOTALL):
        raw = match.group(1)
        try:
            decoded = zlib.decompress(raw)
        except zlib.error:
            continue
        for tm in re.finditer(rb"BT\s(.+?)\sET", decoded, re.DOTALL):
            block = tm.group(1)
            for tj in re.finditer(rb"\(([^)]*)\)", block):
                text_parts.append(tj.group(1).decode("latin-1", errors="replace"))

    text = " ".join(text_parts)
    text = re.sub(r"(?<=\w) (?=\w{1,2} )", "", text)
    return text.strip()


def _extract_markdown(md_bytes: bytes) -> str:
    return md_bytes.decode("utf-8", errors="replace").strip()


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

PDF_NOTE = (
    "[note: PDF extracted with basic stdlib parser -- "
    "word spacing may be approximate]"
)

JINA_NOTE = "[note: fetched via Jina Reader -- output is markdown]"


def _fetch_pdf_basic(url: str) -> tuple[str, str]:
    data = _fetch_bytes(url)
    text = _extract_pdf_basic(data)
    if text:
        return text, PDF_NOTE
    raise FetchError("could not extract text from PDF")


def run_fetch(url: str) -> tuple[str, str | None]:
    """Fetch a URL and return (text, note).

    note is a stderr message (e.g. PDF quality warning) or None.
    Raises FetchError if text cannot be extracted.
    """
    kind = _classify_url(url)

    if kind == "arxiv":
        html_url = _arxiv_to_html(url)
        abs_url = _arxiv_to_abs(url)
        pdf_url = _arxiv_to_pdf(url)

        try:
            data = _fetch_bytes(html_url)
            return _extract_html(data, ARXIV_SELECTORS), None
        except (HTTPError, URLError, OSError):
            pass

        for candidate in [pdf_url, abs_url, url]:
            try:
                text = _fetch_jina(candidate)
                return text, JINA_NOTE
            except (FetchError, HTTPError, URLError, OSError):
                continue

        return _fetch_pdf_basic(pdf_url)

    if kind == "github":
        readme_url = _github_to_raw_readme(url)
        if readme_url:
            data = _fetch_bytes(readme_url)
            return _extract_markdown(data), None
        data = _fetch_bytes(url)
        return _extract_html(data, ARTICLE_SELECTORS), None

    if kind == "pdf":
        try:
            text = _fetch_jina(url)
            return text, JINA_NOTE
        except (FetchError, HTTPError, URLError, OSError):
            return _fetch_pdf_basic(url)

    # Generic HTML -- try Jina first, fall back to local extraction.
    try:
        text = _fetch_jina(url)
        return text, JINA_NOTE
    except (FetchError, HTTPError, URLError, OSError):
        pass

    data = _fetch_bytes(url)
    if data[:5] == b"%PDF-":
        text = _extract_pdf_basic(data)
        if text:
            return text, PDF_NOTE
    return _extract_html(data, ARTICLE_SELECTORS), None


# ---------------------------------------------------------------------------
# PDF download
# ---------------------------------------------------------------------------

def _resolve_pdf_url(url: str) -> str | None:
    """Return a direct PDF URL for the source, or None if unavailable."""
    kind = _classify_url(url)
    if kind == "arxiv":
        return _arxiv_to_pdf(url)
    if kind == "pdf":
        return url
    # HTML and GitHub sources have no PDF to download.
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DOWNLOADS_DIR = Path.home() / "Downloads"


def _resolve_target(target: str) -> tuple[str, str | None]:
    """Resolve a CLI target to (url, ref_name|None)."""
    if target.startswith("http"):
        return target, None
    ref_path = resolve_ref(target)
    if not ref_path:
        raise click.ClickException("not a URL and no matching ref found")
    resolved = get_url(ref_path)
    if not resolved:
        raise click.ClickException("ref found but has no url in front-matter")
    click.echo(f"[resolved: {resolved}]", err=True)
    return resolved, ref_path.stem


def _output_name(ref_name: str | None, url: str) -> str:
    return ref_name or urlparse(url).path.strip("/").replace("/", "_") or "fetch"


@click.command()
@click.argument("target")
@click.option("--save", is_flag=True, help="Save extracted text to ~/Downloads/<name>.txt.")
@click.option("--pdf", is_flag=True, help="Download the raw PDF to ~/Downloads/<name>.pdf.")
def fetch(target: str, save: bool, pdf: bool):
    """Fetch a URL (or ref name) and print extracted text to stdout.

    TARGET can be a URL or the name of a file in refs/ (with or without
    the .md extension).  If it's a ref, the URL is read from front-matter.
    """
    url, ref_name = _resolve_target(target)

    if pdf:
        pdf_url = _resolve_pdf_url(url)
        if not pdf_url:
            raise click.ClickException(
                f"no PDF available for {url} (source type: {_classify_url(url)})"
            )
        data = _fetch_bytes(pdf_url)
        if data[:5] != b"%PDF-":
            raise click.ClickException(f"response from {pdf_url} is not a PDF")
        dest = DOWNLOADS_DIR / f"{_output_name(ref_name, url)}.pdf"
        dest.write_bytes(data)
        click.echo(f"[saved: {dest}]", err=True)
        return

    try:
        text, note = run_fetch(url)
    except Exception as e:
        raise click.ClickException(str(e))
    if note:
        click.echo(note, err=True)

    if save:
        dest = DOWNLOADS_DIR / f"{_output_name(ref_name, url)}.txt"
        dest.write_text(text, encoding="utf-8")
        click.echo(f"[saved: {dest}]", err=True)
    else:
        click.echo(text)
