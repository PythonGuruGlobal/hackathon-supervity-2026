def read_symptoms(user_input: str):
    """
    Takes comma-separated symptoms string
    and returns a cleaned list
    """
    return [s.strip().lower() for s in user_input.split(",")]
