from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

load_dotenv(Path(__file__).resolve().parents[2] / '.env', override=False)
load_dotenv(Path(__file__).resolve().parents[3] / '.env', override=False)

KB_PATH = Path(__file__).resolve().parent / 'kb' / 'orion_kb.json'

@dataclass
class KBEntry:
    id: str
    title: str
    tags: list[str]
    text: str


class OrionQA:
    def __init__(self):
        raw = json.loads(KB_PATH.read_text())
        self.entries = [KBEntry(**r) for r in raw]
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        corpus = [self._doc(e) for e in self.entries]
        self.matrix = self.vectorizer.fit_transform(corpus)
        self.scope_terms = set(
            'orion scenario scenarios sensor sensors ml ai machine learning physics motion tracking track threat critical suspicious public data real data opensky celestrak jpl csis missile missiles aircraft fighter transport cruise ballistic hypersonic asteroid satellite debris drone response responses ui 2d 3d timeline scoring classification profile signature anomaly kalman family families object objects purpose motivation limitation limitations pipeline graphics sprite sprites render chatbot assistant knowledge base q&a qa answer answers generate generation retrieval retrieved context prompt prompts gpt openai gpt4o mini api key responses api scope fallback modal popup expanded panel tooltip tooltips capability intent confidence environment environmental risk posture sensor penalty route endpoint backend frontend fastapi c++ engine feature features legend quick read protected restricted hazard zone zones predicted path map globe camera recenter topdown top-down angled height profile region southern california bay area nevada test range pacific northwest east coast playback play pause step reset speed operations environment weather wind visibility jamming testing add remove selected inspect selected object track dropdown summary sensors catalog model deep dive technical overview response selection ask orion modal overlay popup close x expand panel open system start quick tour how orion works total benign unknown suspicious critical info question mark infotip help how use'.split()
        )
        self.shortcut_map = [
            (['what is orion', 'what does orion do'], ['overview']),
            (['legend', 'what is the legend', 'what is legend', 'legend for', 'what does the legend do'], ['ui_legend', 'ui_map_2d', 'ui_globe_3d']),
            (['total', 'benign', 'unknown count', 'suspicious count', 'critical count', 'top stats', 'statistics', 'stats strip'], ['ui_stats_strip']),
            (['guided mode', 'analyst mode', 'mode toggle'], ['ui_modes']),
            (['start quick tour', 'guided tour', 'intro overlay', 'open system', 'how orion works button'], ['ui_intro_and_tour']),
            (['why did you build', 'motivation', 'purpose'], ['motivation']),
            (['how does the pipeline work', 'pipeline'], ['pipeline', 'scenario_generation', 'physics', 'sensors', 'tracking', 'features', 'cpp_engine']),
            (['what ml', 'what ai', 'machine learning'], ['ml_stack', 'qa_architecture']),
            (['capability', 'what does capability mean'], ['glossary_capability', 'cpp_engine']),
            (['intent', 'what does intent mean'], ['glossary_intent', 'cpp_engine']),
            (['confidence', 'what does confidence mean'], ['glossary_confidence', 'cpp_engine']),
            (['environmental risk', 'what does environmental risk mean'], ['glossary_environment', 'cpp_engine']),
            (['risk posture', 'what does risk posture mean'], ['glossary_risk_posture', 'cpp_engine']),
            (['sensor penalty', 'what does sensor penalty mean'], ['glossary_sensor_penalty', 'sensors']),
            (['public data', 'opensky', 'celestrak', 'jpl', 'csis', 'real data'], ['public_sources', 'real_data_use', 'signature_matching', 'simulated_vs_real']),
            (['missile', 'classify missile', 'missiles'], ['missile_classification', 'critical_logic', 'signature_matching']),
            (['aircraft', 'classify aircraft', 'fighter', 'transport'], ['aircraft_classification', 'signature_matching']),
            (['limitations'], ['limitations', 'simulated_vs_real']),
            (['response panel', 'response options', 'operator response', 'evacuation', 'intercept', 'dispatch inspection', 'stand down'], ['ui_response_panel', 'responses']),
            (['2d and 3d', '3d view', '2d view'], ['ui_map_2d', 'ui_globe_3d', '3d_view', 'graphics']),
            (['timeline', 'event timeline', 'events tab', 'event log'], ['ui_events_timeline', 'events']),
            (['chatbot', 'assistant', 'q&a', 'ask orion', 'how do you answer'], ['ui_ask_orion_panel', 'qa_architecture', 'qna_scope', 'qa_answer_generation']),
            (['how do you generate your answers', 'generate your answers', 'how are answers generated', 'how does the assistant answer', 'how does q&a work', 'how does qa work', 'how does ask orion work', 'answer generation'], ['qa_answer_generation', 'qa_scope_and_fallback', 'backend_api_structure']),
            (['api key', 'gpt-4o-mini', 'gpt4o', 'openai', 'responses api', 'llm'], ['qa_answer_generation', 'qa_scope_and_fallback']),
            (['tooltip', 'tooltips', 'question mark', 'info tip', 'infotip'], ['ui_tooltips', 'tooltips_system', 'frontend_ui_structure']),
            (['expand chat', 'expanded chat', 'expand response', 'popup', 'modal', 'click outside', 'x button', 'overlay'], ['ui_modals_and_expansion', 'response_expanded_panels', 'frontend_ui_structure']),
            (['file structure', 'where is', 'implementation', 'source code', 'project files', 'frontend files', 'backend files'], ['implementation_inventory', 'backend_api_structure', 'frontend_ui_structure']),
            (['scenario switching', 'change scenario', 'reset scenario'], ['ui_scenario_controls', 'scenario_specifics', 'backend_api_structure']),
            (['environment controls', 'weather', 'wind', 'visibility', 'jamming', 'hazard intensity'], ['ui_environment_controls', 'sensors', 'physics']),
            (['testing mode', 'add object', 'remove selected', 'inject object'], ['ui_testing_mode', 'object_families']),
            (['2d map', 'map controls', 'pan', 'zoom', 'recenter 2d'], ['ui_map_2d', 'graphics']),
            (['3d globe', '3d camera', 'camera angle', 'find in 3d', 'above selected', 'height profile'], ['ui_globe_3d', '3d_view']),
            (['region selector', 'regions', 'southern california', 'bay area', 'nevada test range', 'pacific northwest', 'east coast'], ['ui_region_controls']),
            (['playback', 'simulation speed', 'step', 'play', 'pause', 'reset'], ['ui_playback_speed']),
            (['inspect panel', 'selected object', 'track dropdown', 'find in 3d', 'above selected'], ['ui_inspect_panel']),
            (['summary tab', 'why flagged', 'why orion flagged', 'cpa', 'ttz'], ['ui_summary_tab', 'analysis_terms_glossary']),
            (['sensors tab', 'sensor readings', 'simple sensors', 'complex sensors'], ['ui_sensors_tab', 'sensors']),
            (['analysis tab', 'analysis page', 'model probabilities', 'cluster id', 'anomaly score', 'sub scores'], ['ui_analysis_tab', 'analysis_terms_glossary', 'ml_stack']),
            (['catalog tab', 'catalog', 'source links', 'candidate profiles', 'matched sensor values'], ['ui_catalog_tab', 'signature_matching', 'public_sources']),
            (['model tab', 'physics model', 'tracking model', 'prediction model', 'ai model'], ['ui_model_tab', 'pipeline']),
            (['deep dive tab', 'deep dive', 'technical deep dive'], ['ui_deep_dive_tab', 'pipeline', 'ml_stack', 'public_sources']),
            (['object graphics', 'sprites', 'assets', '3d geometry', '2d graphics'], ['object_graphics_and_assets', 'graphics', '3d_view']),
            (['defense motivation', 'war', 'ukraine', 'middle east', 'iran', 'why orion'], ['why_defense_motivation', 'motivation']),
        ]

    def _doc(self, e: KBEntry) -> str:
        return ' '.join([e.title, ' '.join(e.tags), e.text])

    def _tokenize(self, q: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9_]+", q.lower()))

    def _scope_status(self, q: str) -> str:
        ql = (q or '').lower()
        if any(phrase in ql for phrase in [
            'how do you generate', 'how are answers generated', 'how does the assistant',
            'how does ask orion', 'what do you know', 'what can you answer', 'api key',
            'gpt', 'openai', 'llm', 'knowledge base', 'retrieval'
        ]):
            return 'in_scope'
        tokens = self._tokenize(q)
        overlap = len(tokens & self.scope_terms)
        if overlap == 0 and len(tokens) > 2:
            return 'out_of_scope'
        return 'in_scope'

    def retrieve(self, question: str, k: int = 5) -> dict[str, Any]:
        q = (question or '').strip()
        if not q:
            return {'status': 'empty', 'entries': [], 'scores': []}
        ql = q.lower()
        tokens = self._tokenize(q)

        def key_match(key: str) -> bool:
            if ' ' in key:
                return re.search(r"\b" + re.escape(key) + r"\b", ql) is not None
            return key in tokens

        for keys, ids in self.shortcut_map:
            if any(key_match(k) for k in keys):
                by_id = {e.id: e for e in self.entries}
                selected = [by_id[i] for i in ids if i in by_id]
                return {'status': self._scope_status(q), 'entries': selected[:k], 'scores': [1.0] * min(len(selected), k)}

        qvec = self.vectorizer.transform([q])
        scores = cosine_similarity(qvec, self.matrix).ravel()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        selected = [self.entries[i] for i, s in ranked[:k] if s > 0.05]
        selected_scores = [float(s) for _, s in ranked[:k] if s > 0.05]
        status = self._scope_status(q)
        if selected and selected_scores and selected_scores[0] > 0.08:
            status = 'in_scope'
        if not selected and status != 'out_of_scope':
            status = 'low_confidence'
        return {'status': status, 'entries': selected, 'scores': selected_scores}

    def _client(self):
        api_key = os.getenv('OPENAI_API_KEY', '').strip()
        if not api_key or OpenAI is None:
            return None
        base_url = os.getenv('OPENAI_BASE_URL', '').strip() or None
        return OpenAI(api_key=api_key, base_url=base_url)

    def _grounded_context(self, entries: list[KBEntry]) -> str:
        chunks: list[str] = []
        for i, e in enumerate(entries, start=1):
            chunks.append(f"[{i}] {e.title}\nTags: {', '.join(e.tags)}\n{e.text}")
        return "\n\n".join(chunks)

    def _fallback_answer(self, retrieved: dict[str, Any]) -> dict[str, Any]:
        status = retrieved['status']
        entries = retrieved['entries']
        if status == 'empty':
            return {
                'answer': 'Ask about Orion’s pipeline, sensors, ML, public-data integration, object families, scenarios, UI, Q&A architecture, or limitations.',
                'mode': 'fallback', 'used_model': 'local-retrieval', 'sources': []
            }
        if status == 'out_of_scope':
            return {
                'answer': 'That question is outside Orion’s scope. I can answer questions about Orion’s scenarios, sensors, scoring, ML, public-data integration, object families, Q&A architecture, UI, and limitations.',
                'mode': 'fallback', 'used_model': 'local-retrieval', 'sources': []
            }
        if status == 'low_confidence' or not entries:
            return {
                'answer': 'I do not have enough grounded Orion-specific information to answer that reliably. Try asking about the pipeline, sensors, ML, public signatures, physics, scenarios, UI, Q&A architecture, or limitations.',
                'mode': 'fallback', 'used_model': 'local-retrieval', 'sources': []
            }

        entry = entries[0]
        return {
            'answer': entry.text,
            'mode': 'fallback',
            'used_model': 'local-retrieval',
            'sources': [e.title for e in entries[:3]]
        }

    def _llm_answer(self, question: str, retrieved: dict[str, Any]) -> dict[str, Any] | None:
        client = self._client()
        if client is None:
            return None
        entries = retrieved['entries']
        status = retrieved['status']
        context = self._grounded_context(entries)
        sources = [e.title for e in entries]
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip() or 'gpt-4o-mini'

        system_prompt = (
            "You are Orion's grounded project assistant. "
            "Answer ONLY from the retrieved Orion project knowledge and the explicit scope rules below. "
            "Do not invent implementation details. Do not use vague recruiter-style fluff. "
            "Prefer concrete references to actual implemented components such as scenarios, sensors, ML models, scoring logic, signature matching, UI tabs, event timeline, and response panel. "
            "If the retrieved knowledge does not support a claim, say that Orion does not currently document or implement it. "
            "If the question asks how Ask Orion generates answers, uses GPT, retrieves knowledge, uses an API key, or handles scope, treat it as in scope. If the question is outside Orion's scope, say that clearly and list the Orion topics you can cover. "
            "If the question asks for comparisons or design rationale, answer from Orion's documented motivation, architecture, limitations, and implemented behavior. "
            "Keep answers concise and exact. Usually answer in 2-6 sentences. Define terms directly. Do not add throat-clearing, praise, or filler. Use bullets only when the user explicitly asks for a list or comparison."
        )
        user_prompt = (
            f"Question: {question}\n\n"
            f"Scope status: {status}\n\n"
            f"Retrieved Orion knowledge:\n{context if context else '[none]'}\n\n"
            "Return a grounded answer. If out of scope, refuse briefly and redirect to Orion topics."
        )
        try:
            response = client.responses.create(
                model=model,
                temperature=0.0,
                max_output_tokens=220,
                input=[
                    {
                        'role': 'system',
                        'content': [{'type': 'input_text', 'text': system_prompt}],
                    },
                    {
                        'role': 'user',
                        'content': [{'type': 'input_text', 'text': user_prompt}],
                    },
                ],
            )
            text = getattr(response, 'output_text', None)
            if not text:
                text_parts: list[str] = []
                for item in getattr(response, 'output', []) or []:
                    for part in getattr(item, 'content', []) or []:
                        if getattr(part, 'type', '') in {'output_text', 'text'}:
                            text_parts.append(getattr(part, 'text', ''))
                text = ''.join(text_parts)
            text = (text or '').strip()
            if not text:
                return None
            return {
                'answer': text,
                'mode': 'llm-grounded',
                'used_model': model,
                'sources': sources,
            }
        except Exception as e:
            return {
                'answer': f"Orion's LLM assistant could not complete this request, so Orion fell back to its local knowledge base. Error: {str(e)}",
                'mode': 'llm-error',
                'used_model': model,
                'sources': sources,
            }

    def answer(self, question: str) -> dict[str, Any]:
        retrieved = self.retrieve(question)
        llm_result = self._llm_answer(question, retrieved)
        if llm_result and llm_result.get('mode') != 'llm-error':
            return llm_result
        fallback = self._fallback_answer(retrieved)
        if llm_result and llm_result.get('mode') == 'llm-error':
            fallback['answer'] = llm_result['answer'] + "\n\n" + fallback['answer']
            fallback['mode'] = 'fallback-after-llm-error'
            fallback['used_model'] = fallback['used_model'] + ' (after LLM error)'
        return fallback

    def status(self) -> dict[str, Any]:
        client = self._client()
        return {
            'llm_enabled': client is not None,
            'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip() or 'gpt-4o-mini',
            'kb_entries': len(self.entries),
        }
