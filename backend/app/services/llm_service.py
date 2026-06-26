import logging
from groq import Groq
from app import config

# Setup basic logging for this module
logger = logging.getLogger(__name__)

# Initialize clients if keys are present
primary_groq_client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None
fallback_groq_client = Groq(api_key=config.GROQ_FALLBACK_API_KEY) if config.GROQ_FALLBACK_API_KEY else None

SYSTEM_PROMPT = """You are a website-grounded RAG assistant.
Answer ONLY using the retrieved website context.
Never use outside knowledge.
Never invent facts, people, URLs, products, download links, or instructions.
Always include the relevant source URL from the context at the end of your answer.
If the answer is not clearly present in the context, reply exactly:
'I could not find this information in the indexed website pages.'
Keep the answer concise and helpful."""

def _call_groq(client: Groq, question: str, context: str) -> str:
    prompt = f"Website Context:\n{context}\n\nUser Question:\n{question}\n\nAnswer:"
    completion = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )
    return completion.choices[0].message.content

def generate_answer(question: str, context: str) -> tuple[str, str]:
    """
    Generates an answer using primary Groq, falls back to secondary Groq,
    and returns a safe extractive fallback if both fail.
    Returns: (answer_text, generator_name)
    """
    # 1. Try primary Groq
    if primary_groq_client:
        try:
            print("Using Groq primary")
            logger.info("Using Groq primary")
            answer = _call_groq(primary_groq_client, question, context)
            return answer, "groq-primary"
        except Exception as e:
            print(f"Primary Groq failed, trying fallback. Error: {e}")
            logger.warning(f"Primary Groq failed, trying fallback. Error: {e}")
    else:
        print("Primary Groq failed, trying fallback. (No primary key configured)")
        logger.warning("Primary Groq failed, trying fallback. (No primary key configured)")

    # 2. Try fallback Groq
    if fallback_groq_client:
        try:
            print("Using Groq fallback")
            logger.info("Using Groq fallback")
            answer = _call_groq(fallback_groq_client, question, context)
            return answer, "groq-fallback"
        except Exception as e:
            print(f"Fallback Groq failed. Error: {e}")
            logger.error(f"Fallback Groq failed. Error: {e}")
    
    # 3. Extractive Fallback
    print("All LLM providers failed, using extractive fallback")
    logger.error("All LLM providers failed, using extractive fallback")
    safe_message = "AI generation is temporarily unavailable. Please open the retrieved indexed references below."
    return safe_message, "extractive-fallback"
