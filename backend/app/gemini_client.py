import sys
import time
from pathlib import Path

# Add the parent directory of this file to sys.path to support direct execution
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from google import genai
from google.genai import errors
from app import config

def get_client() -> genai.Client:
    """Initializes and returns a Gemini client using the configured API key."""
    return genai.Client(api_key=config.GEMINI_API_KEY)

def check_gemini_connection() -> dict:
    """
    Verifies connectivity to the Gemini API by making a simple generate content request.
    Returns a dictionary indicating success or failure with a details message.
    """
    try:
        client = get_client()
        client.models.generate_content(
            model=config.GEMINI_CHAT_MODEL,
            contents="ping",
        )
        return {
            "status": "success",
            "message": "Successfully connected to the Gemini API."
        }
    except errors.APIError as e:
        error_msg = f"Gemini API Error (Status {e.code}): {e.message}"
        if e.code in (401, 403):
            error_msg = f"Authentication failed: Please check if your GEMINI_API_KEY is valid. (Status {e.code})"
        elif e.code == 429:
            error_msg = "Gemini chat quota is currently unavailable. Please wait and retry, use another available Gemini model, or enable billing."
        elif e.code == 503 or (e.message and "unavailable" in e.message.lower()):
            error_msg = "Gemini service is temporarily busy. Please retry after a few seconds."
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_str = str(e)
        if "503" in error_str or "unavailable" in error_str.lower():
            error_msg = "Gemini service is temporarily busy. Please retry after a few seconds."
        else:
            error_msg = f"Network or system error connecting to Gemini API: {error_str}"
        return {"status": "error", "message": error_msg}

def list_available_models() -> dict:
    """
    Lists all available models under the configured API key.
    """
    try:
        client = get_client()
        models = client.models.list()
        model_list = []
        for model in models:
            model_list.append({
                "name": model.name,
                "display_name": model.display_name,
                "supported_actions": getattr(model, "supported_actions", [])
            })
        return {
            "status": "success",
            "models": model_list
        }
    except errors.APIError as e:
        return {"status": "error", "message": f"Gemini API Error (Status {e.code}): {e.message}"}
    except Exception as e:
        return {"status": "error", "message": f"System error: {str(e)}"}

def generate_chat_response(prompt: str, system_instruction: str = None) -> dict:
    """
    Generates a response using the configured chat model, with retry logic for 503 / UNAVAILABLE.
    """
    max_retries = 3
    backoff_delays = [2.0, 4.0, 8.0]
    
    for attempt in range(max_retries + 1):
        try:
            client = get_client()
            cfg = {}
            if system_instruction:
                cfg["system_instruction"] = system_instruction
                
            response = client.models.generate_content(
                model=config.GEMINI_CHAT_MODEL,
                contents=prompt,
                config=cfg if cfg else None
            )
            return {
                "status": "success",
                "response": response.text
            }
        except errors.APIError as e:
            # Detect 503 or UNAVAILABLE
            is_503 = (e.code == 503) or (e.message and "unavailable" in e.message.lower()) or (e.message and "temporary" in e.message.lower())
            
            if is_503:
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    print(f"[DEBUG] Gemini service temporarily unavailable (503). Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        "status": "error",
                        "error_type": "service_unavailable",
                        "message": "Gemini service is temporarily busy. Please retry after a few seconds."
                    }
            
            # Quota handling (429)
            if e.code == 429:
                return {
                    "status": "error",
                    "error_type": "quota_exhausted",
                    "message": "Gemini chat quota is currently unavailable. Please wait and retry, use another available Gemini model, or enable billing."
                }
                
            return {
                "status": "error",
                "error_type": "api_error",
                "message": f"Gemini API Error (Status {e.code}): {e.message}"
            }
        except Exception as e:
            error_str = str(e)
            is_503 = "503" in error_str or "unavailable" in error_str.lower() or "temporary" in error_str.lower()
            if is_503:
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    print(f"[DEBUG] Gemini service temporarily unavailable (503/Exception). Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        "status": "error",
                        "error_type": "service_unavailable",
                        "message": "Gemini service is temporarily busy. Please retry after a few seconds."
                    }
            return {
                "status": "error",
                "error_type": "system_error",
                "message": f"System error: {error_str}"
            }

def generate_test_response(prompt: str) -> dict:
    """
    Generates a response using the configured chat model.
    """
    return generate_chat_response(prompt)

def create_test_embedding(text: str) -> dict:
    """
    Generates text embeddings using the configured embedding model.
    """
    try:
        client = get_client()
        response = client.models.embed_content(
            model=config.GEMINI_EMBED_MODEL,
            contents=text,
        )
        # Check if embeddings are returned
        if response.embeddings:
            embedding_vector = response.embeddings[0].values
            return {
                "status": "success",
                "embedding": embedding_vector
            }
        else:
            return {"status": "error", "message": "No embeddings were returned by the API."}
    except errors.APIError as e:
        return {"status": "error", "message": f"Gemini API Error (Status {e.code}): {e.message}"}
    except Exception as e:
        return {"status": "error", "message": f"System error: {str(e)}"}

def create_embedding(text: str, task_type: str = "retrieval_document") -> list[float]:
    """
    Creates a text embedding vector using the configured Gemini embedding model.
    Includes validation, retries with exponential backoff, task type support, and error handling.
    """
    if not text:
        raise ValueError("Text content for embedding cannot be empty.")
    
    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("Text content for embedding cannot be empty or only whitespace.")

    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not configured.")

    # Safe-guard the model name format for the SDK
    model_name = config.GEMINI_EMBED_MODEL
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    max_attempts = 3
    delay = 1.0  # initial delay in seconds
    
    for attempt in range(max_attempts):
        try:
            client = get_client()
            response = client.models.embed_content(
                model=model_name,
                contents=cleaned_text,
                config={"task_type": task_type.upper()}
            )
            
            if response.embeddings:
                values = response.embeddings[0].values
                return [float(x) for x in values]
            else:
                raise ValueError("Malformed embedding response: 'embeddings' field is empty or missing.")
                
        except errors.APIError as e:
            is_temporary = e.code in (429, 500, 503, 504)
            if is_temporary and attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
                continue
            
            error_msg = f"Gemini API Error (Status {e.code}): {e.message}"
            if e.code in (401, 403):
                error_msg = f"Authentication failed: Invalid GEMINI_API_KEY. (Status {e.code})"
            elif e.code == 429:
                error_msg = f"Quota exceeded: API rate limits reached. (Status {e.code})"
            raise RuntimeError(error_msg)
            
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"Network or system error during embedding creation: {str(e)}")

def create_embeddings(texts: list[str], batch_size: int = 20, task_type: str = "retrieval_document") -> list[list[float]]:
    """
    Creates multiple text embedding vectors using the configured Gemini embedding model,
    processing in batches of size `batch_size`.
    """
    if not texts:
        return []

    # Clean and validate input list
    validated_texts = []
    for t in texts:
        if not isinstance(t, str):
            raise TypeError("All items in texts list must be strings.")
        cleaned = t.strip()
        if not cleaned:
            raise ValueError("Texts list contains empty or whitespace-only elements.")
        validated_texts.append(cleaned)

    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not configured.")

    # Safe-guard the model name format for the SDK
    model_name = config.GEMINI_EMBED_MODEL
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"

    if batch_size <= 0:
        batch_size = 20

    all_embeddings = []

    # Process in batches
    for i in range(0, len(validated_texts), batch_size):
        batch = validated_texts[i : i + batch_size]
        
        max_attempts = 3
        delay = 1.0
        batch_embeddings = []
        success = False
        
        for attempt in range(max_attempts):
            try:
                client = get_client()
                response = client.models.embed_content(
                    model=model_name,
                    contents=batch,
                    config={"task_type": task_type.upper()}
                )
                
                if response.embeddings and len(response.embeddings) == len(batch):
                    batch_embeddings = [[float(val) for val in emb.values] for emb in response.embeddings]
                    success = True
                    break
                else:
                    raise ValueError(f"Malformed embedding response: expected {len(batch)} embeddings, got {len(response.embeddings) if response.embeddings else 0}")
                    
            except errors.APIError as e:
                is_temporary = e.code in (429, 500, 503, 504)
                if is_temporary and attempt < max_attempts - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                
                error_msg = f"Gemini API Error (Status {e.code}): {e.message}"
                if e.code in (401, 403):
                    error_msg = f"Authentication failed: Invalid GEMINI_API_KEY. (Status {e.code})"
                elif e.code == 429:
                    error_msg = f"Quota exceeded: API rate limits reached. (Status {e.code})"
                raise RuntimeError(error_msg)
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise RuntimeError(f"Network or system error during batch embedding creation: {str(e)}")
        
        if not success:
            raise RuntimeError("Failed to create embeddings for batch after maximum retry attempts.")
            
        all_embeddings.extend(batch_embeddings)

    return all_embeddings

if __name__ == "__main__":
    print("=" * 60)
    print("Running Gemini API Integration self-tests...")
    print("=" * 60)

    # 1. Check connection
    print("\n[Test 1] Checking Gemini connection...")
    conn_result = check_gemini_connection()
    if conn_result["status"] == "success":
        print(f" SUCCESS: {conn_result['message']}")
    else:
        print(f" FAILURE: {conn_result['message']}")
        sys.exit(1)

    # 2. Generate a short response
    prompt = "Explain in one sentence what a RAG pipeline is."
    print(f"\n[Test 2] Generating response for: '{prompt}'...")
    gen_result = generate_test_response(prompt)
    if gen_result["status"] == "success":
        print(f" SUCCESS: {gen_result['response'].strip()}")
    else:
        print(f" FAILURE: {gen_result['message']}")

    # 3. Create one embedding
    text_to_embed = "WebMind chatbot connection test"
    print(f"\n[Test 3] Creating embedding for: '{text_to_embed}'...")
    embed_result = create_test_embedding(text_to_embed)
    if embed_result["status"] == "success":
        vector_snippet = embed_result["embedding"][:5]
        print(f" SUCCESS: Generated embedding vector of length {len(embed_result['embedding'])}.")
        print(f" Vector snippet (first 5 elements): {vector_snippet}")
    else:
        print(f" FAILURE: {embed_result['message']}")

    print("\n" + "=" * 60)
    print("Self-tests completed successfully!")
    print("=" * 60)
