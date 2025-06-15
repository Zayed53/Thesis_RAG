import os
import requests
from bs4 import BeautifulSoup
from langchain.schema import Document

# --- 1. Helper functions to fetch & extract ---

def fetch_junit_writing_tests_section() -> str:
    """
    Fetches exactly the 'Writing tests' section from the JUnit 5 user guide.
    It finds the element with id='writing-tests', then grabs its nearest
    section/div parent to capture the entire section.
    """
    url = "https://junit.org/junit5/docs/5.9.3/user-guide/index.html#writing-tests"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 1. Locate the anchor element
    anchor = soup.find(id="writing-tests")
    if not anchor:
        raise RuntimeError("Couldn't find element with id='writing-tests'")
    
    # 2. Find the nearest section or div.sect1 container
    container = anchor.find_parent("section")
    if not container:
        # fallback: often the guide uses <div class="sect1">
        container = anchor.find_parent("div", class_="sect1")
    if not container:
        raise RuntimeError("Couldn't find parent <section> or <div class='sect1'>")
    
    # 3. Remove navs, scripts, styles, tables of contents
    for bad in container.select("nav, .toc, script, style"):
        bad.decompose()
    
    # 4. Return clean text
    return container.get_text(separator="\n").strip()

def fetch_full_page_text(url: str, selector: dict) -> str:
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.find(**selector)
    if not container:
        # Debug tip: list candidates
        print(f"Available top-level divs:")
        for div in soup.find_all("div", recursive=False):
            print(div.attrs)
        raise RuntimeError(f"Couldn't find content using selector {selector} on {url}")
    for tag in container.select("script, style, aside"):
        tag.decompose()
    return container.get_text(separator="\n").strip()


# --- 2. Define sources & how to extract them ---

SOURCES = [
    {
        "name": "junit_writing_tests",
        "fetcher": fetch_junit_writing_tests_section
    },
    {
    "name": "tutorialspoint_quick_guide",
    "url": "https://www.tutorialspoint.com/junit/junit_quick_guide.htm",
    "selector": {"id": "mainContent"}
    },
    {
        "name": "browserstack_junit5_mockito",
        "url": "https://www.browserstack.com/guide/junit-5-mockito",
        "selector": {"class_": "guide-content"}
    },
    {
        "name": "symflower_junit_examples",
        "url": "https://symflower.com/en/company/blog/2023/how-to-write-junit-test-cases/",
        "selector": {"name": "article"}
    },
]

# --- 3. Create KB directory and in-memory documents list ---

KB_DIR = "junit_kb"
os.makedirs(KB_DIR, exist_ok=True)

kb_documents = []

for src in SOURCES:
    name = src["name"]
    print(f"Processing {name}…")
    # fetch raw text
    if "fetcher" in src:
        text = src["fetcher"]()
    else:
        text = fetch_full_page_text(src["url"], src["selector"])
    # save to disk
    path = os.path.join(KB_DIR, f"{name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    # add to in-memory KB
    kb_documents.append(
        Document(page_content=text, metadata={"source": name})
    )

print(f"\nDone! Saved {len(kb_documents)} documents to `{KB_DIR}` and loaded into memory as `kb_documents`.")

# --- 4. (Optional) inspect your KB ---
for doc in kb_documents:
    print(f"{doc.metadata['source']}: {len(doc.page_content.split())} words")
