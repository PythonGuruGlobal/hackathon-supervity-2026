import os
from openai import OpenAI
from .prompt_templates import PromptTemplates
import sys

# Add project root needed if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

class RAGPipeline:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.templates = PromptTemplates()

    def generate_diagnosis(self, symptoms, retrieved_docs):
        context_str = "\n\n".join(retrieved_docs)
        symptoms_str = ", ".join(symptoms)
        
        user_prompt = self.templates.RAG_USER_PROMPT.format(
            context=context_str,
            symptoms=symptoms_str
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.templates.RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"
