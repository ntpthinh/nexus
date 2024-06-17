SUMMARY_PROMPT = """
You are tasked with providing objective summary, which focuses on presenting the key points and essential information from a text in a neutral and unbiased manner, 
without including personal opinions or interpretations and 
without referring to the document itself for a long document 
while preserving all named entities (people, organizations, locations, etc.) for knowledge graph construction.
Here are the key requirements:

1. Summarize the main points while maintaining object and relationship between entities. 
2. Make the sentence simple with subject-verb-object structure.

# Document
{document}
"""

SYNTHESIZE_ALL_SUMMARIES = """
You are given a list of summaries generated from different parts of a long document. 
Your task is to synthesize these summaries into a coherent and cohesive final summary.
"""
