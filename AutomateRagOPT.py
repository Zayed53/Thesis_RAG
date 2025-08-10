import logging
import transformers

logging.basicConfig(level=logging.INFO)
transformers.utils.logging.set_verbosity_info()

import os
import json
import hashlib
import threading
from typing import List, Optional
import javalang

# from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from ASTstructured import tree_to_json
from Data import *  # preserve your project imports if used elsewhere

# -----------------------
# Configs (tune if needed)
# -----------------------
KB_FOLDER = "junit_kb"
SPLIT_CACHE = "kb_splits.json"
FAISS_INDEX_PATH = "kb_faiss_index"
FAISS_META_PATH = FAISS_INDEX_PATH + ".meta.json"

# You can increase chunk size to reduce vector count for code/text KBs
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 50

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "codellama"
DEFAULT_RETRIEVER_K = 2
DEFAULT_SEARCH_TYPE = "similarity"
DEFAULT_CHAIN_TYPE = "stuff"  # keep same chain_type as your original if desired

# -----------------------
# Global singletons + lock
# -----------------------
_cache_lock = threading.RLock()
_KB_HASH: Optional[str] = None
_SPLITS: Optional[List[Document]] = None
_EMBEDDINGS = None
_VECTORSTORE: Optional[FAISS] = None
_RAG_CHAIN: Optional[RetrievalQA] = None
_OLLAMA_LLM = None

# -----------------------
# Helpers: KB hashing & load
# -----------------------
def hash_knowledge_base(folder_path: str = KB_FOLDER) -> str:
    """
    Fast KB hash: include filenames + mtimes + head of files to detect changes quickly.
    Adjust to read full file contents if you need full integrity.
    """
    hasher = hashlib.md5()
    if not os.path.exists(folder_path):
        return hasher.hexdigest()
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".txt"):
            path = os.path.join(folder_path, filename)
            try:
                hasher.update(filename.encode("utf-8"))
                hasher.update(str(os.path.getmtime(path)).encode("utf-8"))
                with open(path, "rb") as f:
                    # read first 16KB for speed; change if necessary
                    hasher.update(f.read(16384))
            except Exception:
                # ignore unreadable files
                continue
    return hasher.hexdigest()


def load_knowledge_base(folder_path: str = KB_FOLDER) -> List[Document]:
    docs = []
    if not os.path.exists(folder_path):
        return docs
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                content = f.read()
                docs.append(Document(page_content=content, metadata={"source": filename}))
    return docs


# -----------------------
# Split cache handling
# -----------------------
def load_splits_from_cache(kb_hash: str):
    if not os.path.exists(SPLIT_CACHE):
        return None
    try:
        with open(SPLIT_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("hash") != kb_hash:
            return None
        return [Document(page_content=item["content"], metadata=item["metadata"]) for item in data.get("splits", [])]
    except Exception:
        return None


def save_splits_to_cache(splits: List[Document], kb_hash: str):
    data = {
        "hash": kb_hash,
        "splits": [{"content": doc.page_content, "metadata": doc.metadata} for doc in splits]
    }
    try:
        with open(SPLIT_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def split_docs(documents: List[Document], kb_hash: str, force_rebuild: bool = False) -> List[Document]:
    global _SPLITS
    if not force_rebuild:
        cached = load_splits_from_cache(kb_hash)
        if cached:
            _SPLITS = cached
            return cached

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = splitter.split_documents(documents)
    save_splits_to_cache(splits, kb_hash)
    _SPLITS = splits
    return splits


# -----------------------
# Embeddings & FAISS management
# -----------------------
def get_embedding_obj():
    print("Initializing HuggingFace embeddings...")
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        _EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _EMBEDDINGS


def faiss_meta_matches(kb_hash: str) -> bool:
    if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(FAISS_META_PATH):
        return False
    try:
        with open(FAISS_META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return meta.get("hash") == kb_hash
    except Exception:
        return False


def save_faiss_meta(kb_hash: str):
    try:
        with open(FAISS_META_PATH, "w", encoding="utf-8") as f:
            json.dump({"hash": kb_hash}, f)
    except Exception:
        pass


def embed_documents(splits: List[Document], kb_hash: str, force_rebuild: bool = False) -> FAISS:
    """
    Return an in-memory FAISS vectorstore. Load persisted index if meta matches, otherwise build.
    """
    print("Embedding documents into FAISS...")
    global _VECTORSTORE
    embeddings = get_embedding_obj()

    with _cache_lock:
        print("Checking FAISS cache and starting the process...")
        if _VECTORSTORE is not None and not force_rebuild:
            print("Using cached FAISS vectorstore.")
            return _VECTORSTORE

        if not force_rebuild and faiss_meta_matches(kb_hash):
            try:
                print("Loading persisted FAISS index...")
                _VECTORSTORE = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
                return _VECTORSTORE
            except Exception:
                _VECTORSTORE = None  # fallback to rebuild

        print("Creating new FAISS index...")
        # Build FAISS from splits
        _VECTORSTORE = FAISS.from_documents(splits, embeddings)
        try:
            _VECTORSTORE.save_local(FAISS_INDEX_PATH)
            save_faiss_meta(kb_hash)
        except Exception:
            # best-effort persist
            pass

        return _VECTORSTORE


# -----------------------
# Ollama LLM (CodeLlama) singleton
# -----------------------
def get_ollama_llm():
    global _OLLAMA_LLM
    if _OLLAMA_LLM is None:
        _OLLAMA_LLM = Ollama(model=OLLAMA_MODEL, temperature=0.2)
    return _OLLAMA_LLM


# -----------------------
# RAG pipeline creation & caching
# -----------------------
def create_rag_pipeline(force_rebuild: bool = False, retriever_k: int = DEFAULT_RETRIEVER_K, search_type: str = DEFAULT_SEARCH_TYPE, chain_type: str = DEFAULT_CHAIN_TYPE) -> RetrievalQA:
    """
    Initialize (or reuse) a RetrievalQA chain.
    Expensive ops (split/embed/index) are cached and only redone when KB hash changes or force_rebuild=True.
    """
    global _RAG_CHAIN, _KB_HASH, _SPLITS, _VECTORSTORE

    with _cache_lock:
        kb_hash = hash_knowledge_base(KB_FOLDER)
        # If KB hash changed, force rebuild
        if _KB_HASH != kb_hash:
            force_rebuild = True
            _KB_HASH = kb_hash

        # Load KB and splits
        raw_docs = load_knowledge_base()
        splits = split_docs(raw_docs, kb_hash, force_rebuild=force_rebuild)

        # Embed / FAISS
        vectorstore = embed_documents(splits, kb_hash, force_rebuild=force_rebuild)

        # Setup retriever and chain. Always create a new chain if retriever_k changed or chain not set.
        retriever = vectorstore.as_retriever(search_type=search_type, search_kwargs={"k": retriever_k})
        llm = get_ollama_llm()

        if _RAG_CHAIN is None or force_rebuild:
            _RAG_CHAIN = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type=chain_type)
        else:
            # If retriever_k changed between calls, rebuild chain to use new retriever
            # (simple heuristic: check retriever.k via search_kwargs if available)
            try:
                # some vectorstore retrievers may expose search_kwargs; safe to rebuild always if unsure
                _RAG_CHAIN = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type=chain_type)
            except Exception:
                pass

        return _RAG_CHAIN


# -----------------------
# GenerateTest: optimized
# -----------------------
def GenerateTestOPT(sourceCode: str, force_rebuild: bool = False, retriever_k: int = DEFAULT_RETRIEVER_K):
    """
    Parse the provided Java source (you said AST is already optimized),
    prepare a compact prompt "something+json tree", and call the cached RAG chain.
    Returns: (response_text, package, imports)
    """
    print("Generating JUnit tests using optimized RAG pipeline...")
    # Ensure RAG chain is initialized (cached). If KB changed, create_rag_pipeline will rebuild.
    rag_chain = create_rag_pipeline(force_rebuild=force_rebuild, retriever_k=retriever_k)


    print("Rag chain created. Parsing Java source code...")
    tree = javalang.parse.parse(sourceCode)
    json_tree = tree_to_json(tree)
    json_tree_str = json.dumps(json_tree)

    package = json_tree['package']
    imports = json_tree['imports']
    # Compose a small prompt as requested; keep exact structure "something+json tree"
    print ("JSON tree structure:\n", json_tree_str)

    prompt = f"""	
You are a Java testing assistant.
Below is a JSON array of Abstract Syntax Tree for the class under test. Your task is to generate a complete, idiomatic JUnit 5 unit test class for each Public Java method:
```
{json_tree_str}
```
Rules:
- Use @Test from JUnit 5.
- Resolve all the dependencies. Use Mockito (@Mock, Mockito.when(...), verify(...)) for all dependencies.
- Use @BeforeEach for setting up required preconditions before each test method And @AfterEach for cleanup. Use @BeforeAll (static) if setup is required once before all tests.
- Instantiate the class under test using proper constructor.
- For each invocation:
Stub its behavior (when(mock.member(args)).thenReturn(...) for non-void; doNothing().when(...) and verify mehtod call for void ).
- Use Arrange-Act-Assert format.
  -Arrange: Set up inputs, mocks, or stubs.
  -Act: Call the method under test.
  -Assert:  Verify the results.
- Make all test methods public.
- Import only what’s necessary.
- Return only a complete Java test class, no explanation.
- Return Only Code in Response, no other text.
"""

    # Run the RetrievalQA chain (reuses cached retriever & LLM)
    response = rag_chain.run(prompt)

    return response, package, imports


# -----------------------
# Utility: invalidate cache and force rebuild
# -----------------------
def invalidate_and_rebuild_kb():
    """
    Clears in-memory caches and forces a rebuild on next pipeline init.
    Call this after you modify KB files.
    """
    global _KB_HASH, _SPLITS, _VECTORSTORE, _RAG_CHAIN
    with _cache_lock:
        _KB_HASH = None
        _SPLITS = None
        _VECTORSTORE = None
        _RAG_CHAIN = None
    # Optionally warm up:
    return create_rag_pipeline(force_rebuild=True, retriever_k=DEFAULT_RETRIEVER_K)


# -----------------------
# Warmup example for long-running service
# -----------------------
# if __name__ == "__main__":
#     # Warm up once so subsequent GenerateTest calls are fast
#     print("Warming up RAG pipeline...")
#     create_rag_pipeline(force_rebuild=False, retriever_k=DEFAULT_RETRIEVER_K)
#     print("Warmup complete. Call GenerateTest(sourceCode) repeatedly.")
