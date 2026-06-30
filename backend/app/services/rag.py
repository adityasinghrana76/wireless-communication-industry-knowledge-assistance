import httpx
from openai import AsyncOpenAI
from urllib.parse import urlparse

from app.core.config import get_settings
from app.models import Source
from app.schemas import ChatResponse, SourceReference
from app.services.vector_store import VectorStoreService


class RagService:
    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.settings = get_settings()

    async def answer(self, question: str, collection_name: str, top_k: int, provider: str | None) -> ChatResponse:
        contexts = self.vector_store.query(collection_name, question, top_k)
        if not contexts:
            contexts = self._source_contexts(question, top_k)
        prompt = self._build_prompt(question, contexts)
        selected_provider = provider or self.settings.default_llm_provider
        answer = ""
        if selected_provider == "llama" and self.settings.local_llama_base_url:
            answer = await self._try_local_llama(prompt)
        elif self.settings.openai_api_key:
            answer = await self._try_openai(prompt)
        if not answer and contexts:
            answer = self._extractive_answer(question, contexts)
        if not answer:
            answer = "No sources are available yet. Run Search first, then ask again."
        confidence = round(sum(c["score"] for c in contexts) / max(len(contexts), 1), 3)
        sources = [
            SourceReference(
                url=c["metadata"].get("url", ""),
                title=c["metadata"].get("title") or None,
                confidence_score=round(c["score"], 3),
                chunk_id=c["metadata"].get("document_id"),
            )
            for c in contexts
        ]
        return ChatResponse(answer=answer, confidence_score=confidence, sources=sources)

    async def _try_openai(self, prompt: str) -> str:
        try:
            return await self._openai(prompt)
        except Exception:
            return ""

    async def _try_local_llama(self, prompt: str) -> str:
        try:
            return await self._local_llama(prompt)
        except httpx.HTTPError:
            return ""

    def _source_contexts(self, question: str, top_k: int) -> list[dict]:
        sources = (
            self.vector_store.db.query(Source)
            .order_by(Source.retrieved_at.desc())
            .limit(max(top_k * 3, top_k))
            .all()
        )
        stop_terms = {
            "company",
            "companies",
            "supplier",
            "suppliers",
            "vendor",
            "vendors",
            "about",
            "which",
            "what",
            "main",
            "find",
            "list",
            "show",
            "tell",
        }
        query_terms = {term.lower() for term in question.split() if len(term) > 2 and term.lower() not in stop_terms}
        scored: list[tuple[int, Source]] = []
        for source in sources:
            text = " ".join(
                part
                for part in [source.title or "", source.summary or "", source.raw_text or ""]
                if part
            )
            haystack = text.lower()
            score = sum(1 for term in query_terms if term in haystack)
            scored.append((score, source))

        ranked_sources = [source for _, source in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]]
        contexts = []
        for source in ranked_sources:
            text = source.raw_text or source.summary or source.title or source.url
            contexts.append(
                {
                    "text": text[:1400],
                    "metadata": {
                        "url": source.url,
                        "title": source.title or source.url,
                        "document_id": f"source-{source.id}",
                    },
                    "score": min(max((source.credibility_score or 50) / 100, 0.1), 1.0),
                }
            )
        return contexts

    def _extractive_answer(self, question: str, contexts: list[dict]) -> str:
        companies = self._company_summaries(contexts[:6])
        lines = [f"Question: {question}", "", "Main companies / organizations found:"]
        for index, company in enumerate(companies, start=1):
            lines.extend(
                [
                    f"{index}. {company['name']}",
                    f"   - About: {company['about']}",
                    f"   - Evidence: {company['evidence']}",
                    f"   - Source: {company['source']}",
                ]
            )
        lines.extend(
            [
                "",
                "Note: Ye source-backed summary hai. OpenAI quota active hoga to answer aur natural analyst style me synthesize hoga.",
            ]
        )
        return "\n".join(lines)

    def _company_summaries(self, contexts: list[dict]) -> list[dict]:
        summaries: list[dict] = []
        seen: set[str] = set()
        for context in contexts:
            title = context["metadata"].get("title") or context["metadata"].get("url")
            url = context["metadata"].get("url")
            snippet = " ".join(context["text"].split())
            for name in self._company_names(title, url, snippet):
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)
                summaries.append(
                    {
                        "name": name,
                        "about": self._company_about(title, snippet),
                        "evidence": self._shorten(snippet or title, 220),
                        "source": url,
                    }
                )
                if len(summaries) >= 8:
                    return summaries
        if summaries:
            return summaries
        return [
            {
                "name": self._company_name(
                    context["metadata"].get("title") or context["metadata"].get("url"),
                    context["metadata"].get("url"),
                    context["text"],
                ),
                "about": self._company_about(context["metadata"].get("title") or "", context["text"]),
                "evidence": self._shorten(context["text"], 220),
                "source": context["metadata"].get("url"),
            }
            for context in contexts[:5]
        ]

    def _company_names(self, title: str, url: str, text: str) -> list[str]:
        haystack = f"{title} {text}"
        known_names = [
            "Airspan",
            "Nokia",
            "Ericsson",
            "NEC",
            "Cisco",
            "Qualcomm",
            "Keysight",
            "VIAVI",
            "SOLiD",
            "Fujitsu",
            "Taoglas",
            "Benetel",
            "Huawei",
            "Samsung",
            "Texas Instruments",
            "Analog Devices",
            "Kyocera",
            "Eridan",
            "Abside",
            "Mavenir",
            "Parallel Wireless",
            "Radisys",
            "JMA Wireless",
            "Commscope",
            "Comba",
            "Amphenol",
            "Rosenberger",
            "Alpha Wireless",
        ]
        found = [name for name in known_names if name.lower() in haystack.lower()]
        if found:
            return found

        host = (urlparse(url).hostname or "").removeprefix("www.")
        evidence_domains = {
            "lightreading.com",
            "dataintelo.com",
            "fortuneindia.com",
            "tickertape.in",
            "getchip.uk",
            "rfwireless-world.com",
            "stlpartners.com",
            "wikipedia.org",
            "youtube.com",
        }
        if any(host.endswith(domain) for domain in evidence_domains):
            return []
        return [self._company_name(title, url, text)]

    def _company_name(self, title: str, url: str, text: str) -> str:
        host = urlparse(url).hostname or ""
        host = host.removeprefix("www.")
        domain_name = host.split(".")[0].replace("-", " ").title() if host else ""
        known_domains = {
            "airspan.com": "Airspan",
            "nokia.com": "Nokia",
            "ericsson.com": "Ericsson",
            "nec.com": "NEC",
            "cisco.com": "Cisco",
            "qualcomm.com": "Qualcomm",
            "keysight.com": "Keysight",
            "viavisolutions.com": "VIAVI Solutions",
            "solid.com": "SOLiD",
            "fujitsu.com": "Fujitsu",
            "taoglas.com": "Taoglas",
            "ti.com": "Texas Instruments",
            "analog.com": "Analog Devices",
        }
        for domain, name in known_domains.items():
            if host.endswith(domain):
                return name

        haystack = f"{title} {text}"
        known_names = [
            "Airspan",
            "Nokia",
            "Ericsson",
            "NEC",
            "Cisco",
            "Qualcomm",
            "Keysight",
            "VIAVI",
            "SOLiD",
            "Fujitsu",
            "Taoglas",
            "Benetel",
            "Huawei",
            "Samsung",
            "Texas Instruments",
            "Analog Devices",
        ]
        for name in known_names:
            if name.lower() in haystack.lower():
                return name

        for separator in [" - ", " | ", ":"]:
            if separator in title:
                candidate = title.split(separator)[-1 if separator == " | " else 0].strip()
                if 2 <= len(candidate) <= 42:
                    return candidate
        return domain_name or title[:42]

    def _company_about(self, title: str, text: str) -> str:
        lower = f"{title} {text}".lower()
        if "open ran" in lower or "o-ran" in lower or "radio unit" in lower:
            return "Open RAN / radio access network solutions, radio units, or interoperability ecosystem."
        if "antenna" in lower or "massive mimo" in lower:
            return "5G antenna, Massive MIMO, RF, or radio hardware related supplier/vendor."
        if "chipset" in lower or "modem" in lower or "semiconductor" in lower:
            return "5G modem, chipset, RF semiconductor, or device platform supplier."
        if "test" in lower or "measurement" in lower or "validation" in lower:
            return "Wireless test, validation, measurement, or lab infrastructure provider."
        if "operator" in lower or "network" in lower:
            return "Telecom network, infrastructure, or wireless technology organization."
        return "Wireless communication industry organization mentioned in the retrieved evidence."

    def _shorten(self, text: str, limit: int) -> str:
        text = " ".join(text.split())
        if len(text) <= limit:
            return text
        return f"{text[: limit - 3].rstrip()}..."

    def _build_prompt(self, question: str, contexts: list[dict]) -> str:
        context_text = "\n\n".join(
            f"Source: {c['metadata'].get('url')}\nContent: {c['text']}" for c in contexts
        )
        return (
            "You are a wireless communication industry analyst. Answer only from the context. "
            "Make the answer company-first and easy for a non-expert to read. Use this format:\n"
            "Main companies / organizations found:\n"
            "1. Company name\n"
            "   - About: what the company does in simple words\n"
            "   - Evidence: what the source says\n"
            "   - Source: URL\n"
            "Do not dump raw search snippets. If a source is not a company, label it as an organization or evidence source.\n\n"
            f"Question: {question}\n\nContext:\n{context_text}"
        )

    async def _openai(self, prompt: str) -> str:
        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    async def _local_llama(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.settings.local_llama_base_url}/api/generate",
                json={"model": "llama3", "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "")
