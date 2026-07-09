from tavily import TavilyClient
from groq import Groq

from app.config import TAVILY_API_KEY, GROQ_API_KEY

tavily = TavilyClient(api_key=TAVILY_API_KEY)
groq = Groq(api_key=GROQ_API_KEY)


def web_search(query: str):
    try:
        search = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=3,
            include_answer=True
        )

        results = search.get("results", [])

        if not results:
            return "Sorry, I couldn't find any recent information."

        context = ""

        for result in results:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")

            context += f"""
Title: {title}
Content: {content}
Source: {url}

"""

        prompt = f"""
You are a helpful AI assistant.

The user asked:

{query}

Below are live web search results.

{context}

Instructions:
- Answer ONLY using the search results.
- Give a concise, natural answer.
- Combine information from multiple sources if needed.
- Do NOT dump the search results.
- Do NOT list URLs.
- Do NOT mention "search results".
- If the information is uncertain, say so.
- End with:
"According to recent reports."
"""

        response = groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You answer using only the provided web information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(e)
        return "Sorry, I couldn't search the web right now."