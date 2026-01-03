def explain(disease, symptoms, confidence):
    # Low-confidence safeguard
    if confidence < 0.4:
        return {
            "predicted_disease": None,
            "confidence": confidence,
            "input_symptoms": symptoms,
            "explanation": (
                "The system could not determine a disease with sufficient confidence "
                "based on the provided symptoms. Please provide more specific symptoms "
                "or consult a medical professional."
            )
        }

    # High-confidence explanation
    message = (
        f"The prediction is based on the presence of "
        f"{', '.join(symptoms)} which commonly indicate {disease}."
    )

    return {
        "predicted_disease": disease,
        "confidence": confidence,
        "input_symptoms": symptoms,
        "explanation": message
    }
