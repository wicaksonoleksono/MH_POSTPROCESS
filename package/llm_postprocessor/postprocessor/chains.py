"""LangChain chain definitions."""

from langchain_core.runnables import RunnableSequence
from langchain_core.language_model import BaseLanguageModel

from llm_postprocessor.llm.prompts import ANALYSIS_PROMPT, SUMMARIZATION_PROMPT


def create_analysis_chain(
    llm: BaseLanguageModel,
) -> RunnableSequence:
    """Create analysis chain.

    Args:
        llm: Language model to use

    Returns:
        LangChain chain
    """
    return ANALYSIS_PROMPT | llm


def create_summarization_chain(
    llm: BaseLanguageModel,
) -> RunnableSequence:
    """Create summarization chain.

    Args:
        llm: Language model to use

    Returns:
        LangChain chain
    """
    return SUMMARIZATION_PROMPT | llm


def create_combined_chain(
    llm: BaseLanguageModel,
) -> RunnableSequence:
    """Create combined analysis and summarization chain.

    Args:
        llm: Language model to use

    Returns:
        LangChain chain
    """
    analysis_chain = create_analysis_chain(llm)
    summarization_chain = create_summarization_chain(llm)

    def combined(session_data: dict) -> dict:
        analysis = analysis_chain.invoke({"session_data": str(session_data)})
        summary = summarization_chain.invoke({"analysis": analysis})
        return {"analysis": analysis, "summary": summary}

    return combined
