from __future__ import annotations

import json

from app.core.settings import settings
from app.services.llm_client import LLMClient
from app.services.prompt_loader import load_prompt
from app.services.supabase_client import SupabaseService


class KnowledgeExtractionService:
    def __init__(self, llm: LLMClient, supabase: SupabaseService):
        self.llm = llm
        self.supabase = supabase

    async def extract_book(self, book_id: str) -> tuple[int, int]:
        chunks = self.supabase.get_book_chunks(book_id)
        prompt = load_prompt('extract_rules')
        rules_created = 0

        for chunk in chunks:
            user_prompt = json.dumps(
                {
                    'book_id': book_id,
                    'chunk_id': chunk['id'],
                    'content': chunk['content'],
                },
                ensure_ascii=False,
            )
            result = await self.llm.chat_json(prompt, user_prompt, settings.llm_model_extract)
            rules = result.get('rules', [])
            rows = []
            for rule in rules:
                rows.append(
                    {
                        'book_id': book_id,
                        'source_chunk_id': chunk['id'],
                        'rule_type': rule.get('rule_type', 'procedure_rule'),
                        'surface': rule.get('surface'),
                        'fiber': rule.get('fiber'),
                        'stain_type': rule.get('stain_type'),
                        'product': rule.get('product'),
                        'equipment': rule.get('equipment'),
                        'procedure_steps': rule.get('procedure_steps') or [],
                        'dwell_time': rule.get('dwell_time'),
                        'water_temp': rule.get('water_temp'),
                        'agitation_level': rule.get('agitation_level'),
                        'risk': rule.get('risk'),
                        'forbidden_action': rule.get('forbidden_action'),
                        'safety_notes': rule.get('safety_notes'),
                        'expected_result': rule.get('expected_result'),
                        'confidence_score': rule.get('confidence_score'),
                        'source_quote': rule.get('source_quote'),
                    }
                )
            if rows:
                self.supabase.insert_knowledge_rules(rows)
                rules_created += len(rows)

        self.supabase.update_book_status(book_id, 'extracted')
        return len(chunks), rules_created
