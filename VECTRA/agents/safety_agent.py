class SafetyAgent:
    DISCLAIMER = "This system is for educational purposes only. Please consult a licensed medical professional."
    
    def check_safety(self, text):
        # Placeholder for PII or harmful content check
        return True

    def attach_disclaimer(self, response_dict):
        response_dict["disclaimer"] = self.DISCLAIMER
        return response_dict
