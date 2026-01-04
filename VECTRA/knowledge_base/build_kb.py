import pandas as pd
import os
import json

def build_knowledge_base():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_data_path = os.path.join(base_dir, "data", "raw", "disease_symptoms.csv")
    output_path = os.path.join(base_dir, "knowledge_base", "disease_docs.csv")
    
    if not os.path.exists(raw_data_path):
        print(f"Error: Raw data not found at {raw_data_path}")
        return

    # Load raw data
    # Assuming the CSV has columns like 'Disease', 'Symptom_1', 'Symptom_2', ...
    df = pd.read_csv(raw_data_path)
    
    # Check if 'Disease' column exists (adapt based on actual CSV structure)
    # The provided dataset usually has 'Disease' and multiple Symptom columns
    
    # Consolidate symptoms for each disease description
    docs = []
    
    # We group by Disease to aggregate all unique symptoms across potentially multiple rows per disease
    # Or if it's one row per disease occurrence
    
    # Strategy: Create a text description for each row/disease
    
    # Clean headers
    df.columns = [c.strip() for c in df.columns]
    
    for index, row in df.iterrows():
        disease = row.get('Disease')
        if not disease:
            continue
            
        # Collect non-null symptoms
        symptoms = []
        for col in df.columns:
            if col != 'Disease':
                val = str(row[col])
                if val and val.lower() != 'nan':
                    symptoms.append(val.strip())
        
        # Create a rich text representation
        symptom_text = ", ".join(symptoms)
        text_content = f"Disease: {disease}. Symptoms include: {symptom_text}."
        
        docs.append({
            "id": f"{disease}_{index}",
            "disease": disease,
            "text": text_content,
            "symptoms": symptom_text
        })
    
    # Save to knowledge base CSV
    kb_df = pd.DataFrame(docs)
    kb_df.to_csv(output_path, index=False)
    print(f"Knowledge base built with {len(kb_df)} documents at {output_path}")

if __name__ == "__main__":
    build_knowledge_base()
