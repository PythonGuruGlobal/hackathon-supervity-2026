class ExplanationAgent:
    def format_explanation(self, disease, confidence, symptoms):
        return (
            f"Based on the symptoms provided ({', '.join(symptoms)}), "
            f"there is a {confidence*100:.1f}% probability of {disease}."
        )

    def format_rag_explanation(self, llm_response):
        return llm_response
