import os
import httpx


def main() -> None:
    key = os.getenv("GROQ_API_KEY")
    print("key_set", bool(key))
    if not key:
        print("missing GROQ_API_KEY")
        return

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "You are a test."},
            {"role": "user", "content": "Say OK"},
        ],
    }
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=20.0,
    )
    print("status", resp.status_code)
    print("body_prefix", resp.text[:200])


if __name__ == "__main__":
    main()
