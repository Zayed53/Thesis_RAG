import os
import json
import hashlib
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from ASTstructured import tree_to_json
import javalang
import json
from Data import *

# Configs
KB_FOLDER = "junit_kb"
SPLIT_CACHE = "kb_splits.json"
FAISS_INDEX_PATH = "kb_faiss_index"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

def hash_knowledge_base(folder_path):
    hasher = hashlib.md5()
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()

def load_knowledge_base(folder_path=KB_FOLDER):
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                content = f.read()
                docs.append(Document(page_content=content, metadata={"source": filename}))
    return docs

def save_splits_to_cache(splits, kb_hash):
    data = {
        "hash": kb_hash,
        "splits": [{"content": doc.page_content, "metadata": doc.metadata} for doc in splits]
    }
    with open(SPLIT_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_splits_from_cache(kb_hash):
    if not os.path.exists(SPLIT_CACHE):
        return None
    with open(SPLIT_CACHE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("hash") != kb_hash:
        return None
    return [Document(page_content=item["content"], metadata=item["metadata"]) for item in data["splits"]]

def split_docs(documents, force_rebuild=False):
    kb_hash = hash_knowledge_base(KB_FOLDER)
    
    if not force_rebuild:
        cached_splits = load_splits_from_cache(kb_hash)
        if cached_splits:
            print("Loaded chunked splits from cache.")
            return cached_splits
    
    print("Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = splitter.split_documents(documents)
    save_splits_to_cache(splits, kb_hash)
    return splits

def embed_documents(splits, force_rebuild=False):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if not force_rebuild and os.path.exists(FAISS_INDEX_PATH):
        print("Loading existing FAISS index...")
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

    
    print("Creating FAISS index...")
    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    return vectorstore

def get_ollama_llm():
    return Ollama(model="codellama", temperature=0.2)

def create_rag_pipeline(force_rebuild=False, retriever_k=4, search_type="similarity"):
    print("Loading knowledge base...")
    raw_docs = load_knowledge_base()
    print(f"Loaded {len(raw_docs)} documents.")

    print("Splitting documents...")
    splits = split_docs(raw_docs, force_rebuild=force_rebuild)

    print("Embedding documents...")
    vectorstore = embed_documents(splits, force_rebuild=force_rebuild)

    print("Setting up retriever...")
    retriever = vectorstore.as_retriever(search_type=search_type, search_kwargs={"k": retriever_k})

    print("Initializing LLM and RAG pipeline...")
    llm = get_ollama_llm()
    rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")

    return rag_chain



rag_chain = create_rag_pipeline(force_rebuild=False, retriever_k=4)

# java_method = """

# """

tree = javalang.parse.parse(Java_sourceCode)
json_tree = tree_to_json(tree)
json_tree_str = json.dumps(json_tree)

prompt = f"""	
You are a Java testing assistant.

Below is a JSON array of method‐metadata for the class under test. Your task is to generate a complete, idiomatic JUnit 5 unit test class for each following Java method:

```json
{json_tree_str}

```
Rules:
1. Use @Test from JUnit 5.
2. Resolve all the dependencies. Use Mockito (@Mock, Mockito.when(...), verify(...)) for all dependencies.
3. Use @BeforeEach for setting up required preconditions before each test method And @AfterEach for cleanup. Use @BeforeAll (static) if setup is required once before all tests.
4. For each invocation:
Stub its behavior (when(mock.member(args)).thenReturn(...) for non-void; doNothing().when(...) and verify mehtod call for void ).
5. Use Arrange-Act-Assert format.
  -Arrange: Set up inputs, mocks, or stubs.
  -Act: Call the method under test.
  -Assert:  Verify the results.
6. Make all test methods public.
7. Import only what’s necessary: JUnit 5, Mockito, and the class under test.
8. Return only a complete Java test class, no explanation.

`
"""
response = rag_chain.run(prompt)
# print("Generated JUnit test cases:\n", response)
print("Generated JUnit test cases successfully. Now saving to file...")
# Save the generated test cases to a Test.java file
with open("TestNew.java", "w", encoding="utf-8") as f:
    f.write(response)

print("JUnit test cases saved to Test.java")
