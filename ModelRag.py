import os
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import Ollama
from langchain.chains import RetrievalQA

# 1. Load text files into LangChain Documents
def load_knowledge_base(folder_path="junit_kb"):
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                content = f.read()
                docs.append(Document(page_content=content, metadata={"source": filename}))
    return docs

# 2. Split documents into chunks  ///explain
def split_docs(documents, chunk_size=800, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)

# 3. Use sentence-transformers for local embeddings
def embed_documents(splits):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  # Efficient & fast
    vectorstore = FAISS.from_documents(splits, embeddings)
    return vectorstore

# 4. Set up Ollama (CodeLlama)
def get_ollama_llm():
    return Ollama(model="codellama", temperature=0.2)

# 5. Create the RAG QA chain
def create_rag_pipeline():
    print("Loading knowledge base...")
    raw_docs = load_knowledge_base()
    print(f"Loaded {len(raw_docs)} documents")

    print("Splitting documents...")
    splits = split_docs(raw_docs)

    print("Embedding & creating vectorstore...")
    vectorstore = embed_documents(splits)

    print("Setting up RAG pipeline...")
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4}) #///explain
    llm = get_ollama_llm()
    rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")

    return rag_chain

# 6. Run a query
if __name__ == "__main__":
    rag_pipeline = create_rag_pipeline()

    print("\nRAG system ready! Ask a question:")

    java_metadata = [
  {
    "focal_class": "OrderProcessor",
    "method_name": "processOrder",
    "parameters": [
      "String orderId"
    ],
    "return_type": "boolean",
    "dependencies": [
      "inventoryService",
      "paymentService"
    ],
    "invocations": [
      {
        "member": "charge",
        "qualifier": "paymentService",
        "arguments": [
          "orderId"
        ]
      },
      {
        "member": "reserveItems",
        "qualifier": "inventoryService",
        "arguments": [
          "orderId"
        ]
      }
    ]
  },
  {
    "focal_class": "OrderProcessor",
    "method_name": "cancelOrder",
    "parameters": [
      "String orderId"
    ],
    "return_type": "void",
    "dependencies": [
      "inventoryService",
      "paymentService"
    ],
    "invocations": [
      {
        "member": "refund",
        "qualifier": "paymentService",
        "arguments": [
          "orderId"
        ]
      },
      {
        "member": "releaseItems",
        "qualifier": "inventoryService",
        "arguments": [
          "orderId"
        ]
      }
    ]
  },
  {
    "focal_class": "OrderProcessor",
    "method_name": "getOrderStatus",
    "parameters": [
      "String orderId"
    ],
    "return_type": "String",
    "dependencies": [],
    "invocations": []
  }
]
    java_method = """
    public class OrderProcessor {


        public boolean processOrder(String orderId) {
            boolean paymentSuccess = paymentService.charge(orderId);
            if (!paymentSuccess) {
                return false;
            }
            inventoryService.reserveItems(orderId);
            return true;
        }

        public void cancelOrder(String orderId) {
            paymentService.refund(orderId);
            inventoryService.releaseItems(orderId);
        }

        public String getOrderStatus(String orderId) {
            return "Processed";
        }
    }
    """

    prompt = f"""
You are a Java testing assistant.

Your task is to generate a complete, idiomatic JUnit 5 unit test class for each following Java method:

```java
{java_method}

Rules:
1. Use @Test from JUnit 5.
2. use @Test anotation from org.junit.jupiter.api.Test.
3. make All the method public.
4 Resolve all the dependencies.
6. Stub the dependancies/called methods behavior.
7. Create test in arrange assert act format.
Return only the Java test class.
"""
    prompt2 = f"""	
You are a Java testing assistant.

Below is a JSON array of method‐metadata for the class under test. Your task is to generate a complete, idiomatic JUnit 5 unit test class for each following Java method:

```json
{java_metadata}

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
    answer = rag_pipeline.run(prompt2)
    print("Generated test case\n")
    print(answer)





# Instructions:

# Use @Test from JUnit 5.

# Use assertions from org.junit.jupiter.api.Assertions.

# Include at least two test cases: one positive and one negative.

# Assume the method belongs to a class named MyClass.

# Use good naming conventions for test methods.