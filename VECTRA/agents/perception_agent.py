class PerceptionAgent:
    def process_input(self, raw_symptoms):
        """
        Parses and cleans input symptoms.
        Args:
            raw_symptoms (list or str): User input.
        Returns:
            list: Cleaned list of symptoms.
        """
        if isinstance(raw_symptoms, str):
            symptoms = raw_symptoms.split(",")
        else:
            symptoms = raw_symptoms
            
        cleaned = [s.strip() for s in symptoms if s.strip()]
        return cleaned
