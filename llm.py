
import os
import time
import uuid

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from llama_index.core import  KnowledgeGraphIndex, Settings, StorageContext, VectorStoreIndex, get_response_synthesizer
from llama_index.core.schema import Node, NodeRelationship, NodeWithScore
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore, IndexManagement, MetadataIndexFieldType
from llama_index_client import RelatedNodeInfo, TextNode

from prompts import SUMMARY_PROMPT


api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_ENDPOINT")
api_version = os.getenv("API_VERSION")
index_name = "vector"
search_service_api_version = "2023-11-01"
search_service_api_key = os.getenv("AZURE_SEARCH_API_KEY")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")

username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
url = os.getenv("NEO4J_URL")
database = os.getenv("NEO4J_DATABASE")

graph_store = Neo4jGraphStore(
    username=username,
    password=password,
    url=url,
    database=database,
)
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
    vector_store=vector_store, graph_store=graph_store)
vector_index = VectorStoreIndex.from_documents(
    [], storage_context=storage_context)
graph_index = KnowledgeGraphIndex.from_documents(
    [], storage_context=storage_context, max_triplets_per_chunk=2, include_embedding=True)
query_engine = graph_index.as_query_engine(
    include_text=False, response_mode="tree_summarize")

default_retriever = vector_index.as_retriever(
    vector_store_query_mode=VectorStoreQueryMode.DEFAULT)
hybrid_retriever = vector_index.as_retriever(
    vector_store_query_mode=VectorStoreQueryMode.HYBRID)
semantic_retriever = vector_index.as_retriever(
    vector_store_query_mode=VectorStoreQueryMode.SEMANTIC_HYBRID)


def insert_vector_index(text: str, doc_id: str = None, metadata_fields: dict = None):
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

    text_splitter = SentenceSplitter(chunk_size=1024)
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


def summarize_document(full_text: str, summary_query: str = None, metadata=None):
    from llama_index.core.node_parser import SentenceSplitter

    text_splitter = SentenceSplitter(chunk_size=1024)
    text_chunks = text_splitter.split_text(full_text)
    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize", use_async=True
    )
    if not summary_query:
        summary_query = SUMMARY_PROMPT
    if len(text_chunks) > 1:
        summaries = []
        print('text_chunks', len(text_chunks))
        for text_chunk in text_chunks:
            response = response_synthesizer.synthesize(
                summary_query, nodes=[
                    NodeWithScore(
                        node=Node(text=text_chunk),
                        score=1
                    )
                ]
            )
            time.sleep(0.5)
            summaries.append(response)
        return '\n'.join(summaries)

    else:
        response = response_synthesizer.synthesize(
            summary_query, nodes=[
                NodeWithScore(
                    node=Node(text=text_chunk),
                    score=1
                )
            ]
        )
        return response


def handle_graph_document(full_text: str, metadata_fields: dict = None):
    summary = summarize_document(full_text)
    relationship_tuples = extract_relationship(summary)
    for relationship_tuple in relationship_tuples:
        node = Node(text=summary, metadata=metadata_fields)
        graph_index.upsert_triplet_and_node(relationship_tuple, node)


def search_graph(query: str):
    return graph_index.as_query_engine().query(query)


def process_text(text: str):
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.ents]


def extract_relationship(text: str):
    from spacy_llm.util import assemble
    nlp = assemble("spacy.cfg")

    documents = process_text(text)
    relationship_tuples = []
    for document in documents:
        doc = nlp(document)
        for r in doc._.rel:
            relationship_tuples.append(
                (doc.ents[r.dep], r.relation, doc.ents[r.dest]))

    return relationship_tuples


def full_text_search(query: str):
    response = search_client.search(search_text=query)
    return response


def semantic_search(query: str):
    response = semantic_retriever.retrieve(query)
    return response


def ask_over_doc(query: str):
    response = llm.ask(query)
    return response
