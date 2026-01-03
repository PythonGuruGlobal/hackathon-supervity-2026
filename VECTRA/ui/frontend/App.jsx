import React, { useState } from 'react';

function App() {
    const [symptoms, setSymptoms] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        const symptomList = symptoms.split(',').map(s => s.trim()).filter(s => s);

        try {
            const response = await fetch('http://localhost:8000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ symptoms: symptomList }),
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to fetch prediction');
        }
        setLoading(false);
    };

    return (
        <div className="container">
            <header className="header">
                <h1>VECTRA AI</h1>
                <p>Advanced Disease Prediction System</p>
            </header>

            <main>
                <form onSubmit={handleSubmit} className="symptom-form">
                    <label>Enter Symptoms (comma separated):</label>
                    <input
                        type="text"
                        value={symptoms}
                        onChange={(e) => setSymptoms(e.target.value)}
                        placeholder="e.g. fever, cough, fatigue"
                        required
                    />
                    <button type="submit" disabled={loading}>
                        {loading ? 'Analyzing...' : 'Analyze Symptoms'}
                    </button>
                </form>

                {result && (
                    <div className="results-panel">
                        <div className="status-bar">
                            <span className="badge confidence">
                                Confidence: {(result.confidence * 100).toFixed(1)}%
                            </span>
                            {result.used_llm && (
                                <span className="badge llm">LLM Augmented</span>
                            )}
                        </div>

                        <div className="predictions">
                            <h3>Top Predictions</h3>
                            <ul>
                                {result.top_5_predictions.map(([disease, prob], idx) => (
                                    <li key={idx}>
                                        <strong>{disease}</strong> - {(prob * 100).toFixed(1)}%
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div className="explanation">
                            <h3>Analysis</h3>
                            <p>{result.explanation}</p>
                        </div>

                        <div className="disclaimer">
                            {result.disclaimer}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
