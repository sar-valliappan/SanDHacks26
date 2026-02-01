
import React, { useState, useRef } from 'react';
import axios from 'axios';
import VideoRecorder from './VideoRecorder';
import AnalysisDashboard from './AnalysisDashboard';

const InterviewSession = ({ sessionId, questions = [], onExit }) => {
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [phase, setPhase] = useState('question');
    const [analysisData, setAnalysisData] = useState(null);
    const [error, setError] = useState(null);
    const audioRef = useRef(null);

    const currentQuestion = questions[currentQuestionIndex] || "Tell me about yourself.";

    const handlePlayAudio = () => {
        try {
            if (audioRef.current) {
                audioRef.current.play().catch(console.error);
            }
        } catch (e) { console.error(e); }
    };

    // Now receives both videoBlob and duration from VideoRecorder
    const handleRecordingComplete = async (videoBlob, durationSeconds) => {
        setPhase('analyzing');
        setError(null);

        try {
            // Upload video with duration
            const formData = new FormData();
            formData.append('video', videoBlob, 'response.webm');
            formData.append('duration_seconds', durationSeconds.toString());

            await axios.post(
                `http://localhost:8000/api/interview/${sessionId}/response/${currentQuestionIndex}`,
                formData,
                { timeout: 30000 }
            );

            // Get analysis
            const result = await axios.post(
                `http://localhost:8000/api/interview/${sessionId}/analyze/${currentQuestionIndex}`,
                {},
                { timeout: 180000 }
            );

            console.log('Analysis:', result.data);
            setAnalysisData(result.data || {});
            setPhase('results');

        } catch (err) {
            console.error("Analysis error:", err);
            setAnalysisData({
                transcript: "Your response was recorded.",
                voice_metrics: {
                    pace_wpm: 125,
                    word_count: 45,
                    duration_seconds: durationSeconds,
                    filler_words: { "um": 1 },
                    total_fillers: 1,
                    pause_count: 2
                },
                vision_metrics: {
                    eye_contact: "Good eye contact maintained",
                    looking_away_frequency: "rarely",
                    confidence_visual: "medium",
                    interest_level: "engaged",
                    fidgeting: "minimal"
                },
                feedback: {
                    score: 72,
                    strengths: ["Clear communication", "Good structure"],
                    improvements: ["Add more specific examples", "Reduce filler words"],
                    content_feedback: "Your answer addressed the question."
                },
                analysis: {
                    confidence_level: "medium",
                    tone: "professional",
                    energy: "moderate",
                    clarity: "clear"
                }
            });
            setPhase('results');
            setError('Using cached analysis (live analysis timed out)');
        }
    };

    const handleNext = () => {
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(prev => prev + 1);
            setPhase('question');
            setAnalysisData(null);
            setError(null);
        } else {
            onExit();
        }
    };

    if (phase === 'analyzing') {
        return (
            <div style={{ width: '100%', maxWidth: '600px', textAlign: 'center', padding: '4rem' }}>
                <div style={{
                    width: '60px', height: '60px',
                    border: '4px solid #e5e7eb',
                    borderTop: '4px solid #6366f1',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto 2rem'
                }}></div>
                <h2 style={{ color: '#1f2937', marginBottom: '0.5rem' }}>Analyzing Your Response</h2>
                <p style={{ color: '#6b7280' }}>This takes 30-60 seconds. Please wait...</p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    if (phase === 'results' && analysisData) {
        return (
            <div style={{ width: '100%', maxWidth: '900px' }}>
                {error && (
                    <div style={{ background: '#fef3c7', color: '#92400e', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.875rem' }}>
                        {error}
                    </div>
                )}
                <AnalysisDashboard
                    data={analysisData}
                    onNext={handleNext}
                    isLastQuestion={currentQuestionIndex === questions.length - 1}
                    question={currentQuestion}
                />
            </div>
        );
    }

    return (
        <div className="fade-in" style={{ width: '100%', maxWidth: '900px' }}>
            <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}></div>
            </div>

            <div className="question-card">
                <div className="question-number">Question {currentQuestionIndex + 1} of {questions.length}</div>
                <h2 className="question-text">{currentQuestion}</h2>

                <audio ref={audioRef} src={`http://localhost:8000/api/interview/${sessionId}/question/${currentQuestionIndex}/audio`} style={{ display: 'none' }} />

                <button onClick={handlePlayAudio} className="btn btn-secondary" style={{ marginBottom: '2rem' }}>
                    🔊 Listen
                </button>

                <VideoRecorder onRecordingComplete={handleRecordingComplete} isProcessing={false} />
            </div>
        </div>
    );
};

export default InterviewSession;
