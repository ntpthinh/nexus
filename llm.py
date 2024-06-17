
import os
import uuid

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeRelationship
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore, IndexManagement, MetadataIndexFieldType
from llama_index_client import RelatedNodeInfo, SentenceSplitter, TextNode


api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_ENDPOINT")
api_version = os.getenv("API_VERSION")
index_name = "vector"
search_service_api_version = "2023-11-01"
search_service_api_key = os.getenv("AZURE_SEARCH_API_KEY")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")

llm = AzureOpenAI(
    deployment_name="gpt35",
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version)
Settings.llm = llm
credentials = AzureKeyCredential(search_service_api_key)

index_client = SearchIndexClient(
    endpoint=search_endpoint,  credential=credentials)
search_client = SearchClient(
    endpoint=search_endpoint, index_name=index_name, credential=credentials)

search_index_client = SearchClient(
    endpoint=search_endpoint, index_name=index_name, credential=credentials)
embed_model = AzureOpenAIEmbedding(
    model="text-embedding-ada-002",
    deployment_name="embedding",
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)
Settings.embed_model = embed_model
metadata_fields = {
    "author": "author",
    "theme": ("topic", MetadataIndexFieldType.STRING),
    "director": "director",
}
vector_store = AzureAISearchVectorStore(
    search_or_index_client=index_client,
    filterable_metadata_field_keys=metadata_fields,
    index_name=index_name,
    index_management=IndexManagement.CREATE_IF_NOT_EXISTS,
    id_field_key="id",
    chunk_field_key="chunk",
    embedding_field_key="embedding",
    embedding_dimensionality=1536,
    metadata_string_field_key="metadata",
    doc_id_field_key="doc_id",
    language_analyzer="en.lucene",
    vector_algorithm_type="exhaustiveKnn",
)
storage_context = StorageContext.from_defaults(
    vector_store=vector_store)
index = VectorStoreIndex.from_documents(
    [], storage_context=storage_context)
query_engine = index.as_query_engine()

default_retriever = index.as_retriever(
    vector_store_query_mode=VectorStoreQueryMode.DEFAULT)
hybrid_retriever = index.as_retriever(
    vector_store_query_mode=VectorStoreQueryMode.HYBRID)
semantic_retriever = index.as_retriever(
    vector_store_query_mode=VectorStoreQueryMode.SEMANTIC_HYBRID)


def insert_index(text: str, doc_id: str = None, metadata_fields: dict = None):
    search_client.upload_documents(documents=[
        {
            "id": doc_id,
            "chunk": text,
            "metadata": {
                "author": "author",
                "topic": "topic",
                "director": "director"
            }
        }
    ])

    text_splitter = SentenceSplitter()
    text_chunks = text_splitter.split_text(text)
    nodes = []
    if not metadata_fields:
        metadata_fields = {}
    if not doc_id:
        doc_id = str(uuid.uuid4())
    for idx, text_chunk in enumerate(text_chunks):
        node = TextNode(
            text=text_chunk,
            relationships={
                NodeRelationship.SOURCE: RelatedNodeInfo(
                    node_id=doc_id
                )
            }
        )
        if metadata_fields:
            node.metadata.update(metadata_fields)
        nodes.append(node)

    for node in nodes:
        node_embedding = embed_model.get_text_embedding(
            node.get_content()
        )
        node.embedding = node_embedding

    vector_store.add(nodes)


def full_text_search(query: str):
    response = search_client.search(search_text=query)
    return response

def semantic_search(query: str):
    response = semantic_retriever.retrieve(query)
    return response

def ask_over_doc(query: str):
    response = llm.ask(query)
    return response
