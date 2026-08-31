import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from api.gemini_pool import gemini_pool

logger = logging.getLogger(__name__)

def generate_content_with_fallback(
    prompt: str,
    system_instruction: Optional[str] = None,
    json_mode: bool = False,
    temperature: float = 0.2,
    timeout: int = 25
) -> Dict[str, Any]:
    """
    Tries multiple AI providers in sequence: Gemini -> Groq -> OpenRouter -> Ollama.
    """
    
    # 1. Gemini
    if gemini_pool.total_keys > 0:
        try:
            resp = gemini_pool.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                json_mode=json_mode,
                temperature=temperature,
                timeout=timeout
            )
            text = resp.get("text", "").strip()
            if text:
                return {"text": text, "source": "gemini", "model": resp.get("model", "gemini")}
        except Exception as e:
            logger.warning(f"[UniversalPool] Gemini falhou: {e}")

    # 2. Groq
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and len(groq_key) > 15 and not groq_key.lower().startswith(("dummy", "test", "gsk_test")):
        try:
            from groq import Groq
            client = Groq(api_key=groq_key, timeout=timeout, max_retries=1)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
                if json_mode:
                    messages[0]["content"] += " Você responde apenas em JSON válido."
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "messages": messages,
                "model": "llama-3.3-70b-versatile",
                "temperature": temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            completion = client.chat.completions.create(**kwargs)
            text = completion.choices[0].message.content.strip()
            if text:
                return {"text": text, "source": "groq", "model": "llama-3.3-70b-versatile"}
        except Exception as e:
            logger.warning(f"[UniversalPool] Groq falhou: {e}")

    # 3. OpenRouter
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key and len(openrouter_key) > 15:
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
                if json_mode:
                    messages[0]["content"] += " Você responde apenas em JSON válido."
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": "google/gemini-2.5-flash", # Modelo padrão rápido e barato
                "messages": messages,
                "temperature": temperature
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
                
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "MedQuest"
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data.get("choices", [])[0].get("message", {}).get("content", "").strip()
                if text:
                    return {"text": text, "source": "openrouter", "model": payload["model"]}
        except Exception as e:
            logger.warning(f"[UniversalPool] OpenRouter falhou: {e}")

    # 4. Ollama (Local)
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        url = f"{ollama_host}/api/chat"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
            if json_mode:
                messages[0]["content"] += " Você responde apenas em JSON válido."
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": os.environ.get("OLLAMA_MODEL", "llama3.2"),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if json_mode:
            payload["format"] = "json"
            
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data.get("message", {}).get("content", "").strip()
            if text:
                return {"text": text, "source": "ollama", "model": payload["model"]}
    except Exception as e:
        logger.warning(f"[UniversalPool] Ollama falhou: {e}")

    raise RuntimeError("Todos os provedores de IA falharam (Gemini, Groq, OpenRouter, Ollama).")
