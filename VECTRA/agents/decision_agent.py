class DecisionAgent:
    def decide_route(self, confidence, threshold=0.6):
        """
        Decides whether to route to ML Direct or RAG fallback.
        """
        if confidence >= threshold:
            return "ML_DIRECT"
        else:
            return "RAG_FALLBACK"
