
import React, { useState } from 'react';
import axios from 'axios';

const SetupForm = ({ onComplete }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [jobDescription, setJobDescription] = useState('');
    const [resume, setResume] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!jobDescription || !resume) {
            alert("Please provide both Job Description and Resume.");
            return;
        }

        setIsLoading(true);
        try {
            const formData = new FormData();
            formData.append('job_description', jobDescription);
            formData.append('resume', resume);

            const response = await axios.post('http://localhost:8000/api/interview/init', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            onComplete(response.data);
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to start session. Is backend running?");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="card fade-in">
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label">Job Description</label>
                    <textarea
                        className="form-textarea"
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="Paste the job description or role you're applying for..."
                    />
                </div>

                <div className="form-group">
                    <label className="form-label">Resume (PDF)</label>
                    <div className="file-upload">
                        <input
                            type="file"
                            accept=".pdf"
                            onChange={(e) => setResume(e.target.files[0])}
                        />
                        <div className="file-upload-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                            </svg>
                        </div>
                        {resume ? (
                            <span className="file-upload-name">{resume.name}</span>
                        ) : (
                            <span className="file-upload-text">Click to upload or drag and drop</span>
                        )}
                    </div>
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={isLoading}>
                    {isLoading ? (
                        <>
                            <div className="spinner"></div>
                            Generating...
                        </>
                    ) : (
                        'Start Interview'
                    )}
                </button>
            </form>
        </div>
    );
};

export default SetupForm;
