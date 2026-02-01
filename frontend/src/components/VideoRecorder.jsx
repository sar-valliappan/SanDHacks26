
import React, { useState, useRef } from 'react';

const VideoRecorder = ({ onRecordingComplete, isProcessing }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [hasRecording, setHasRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const mediaRecorderRef = useRef(null);
    const videoRef = useRef(null);
    const chunksRef = useRef([]);
    const startTimeRef = useRef(null);
    const timerRef = useRef(null);

    const startRecording = async () => {
        try {
            chunksRef.current = [];
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            videoRef.current.srcObject = stream;
            videoRef.current.muted = true;

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                videoRef.current.srcObject = null;
                videoRef.current.src = url;
                videoRef.current.muted = false;
                videoRef.current.controls = true;
                setHasRecording(true);

                // Stop timer
                if (timerRef.current) {
                    clearInterval(timerRef.current);
                }
            };

            // Start recording
            mediaRecorder.start();
            startTimeRef.current = Date.now();
            setRecordingTime(0);

            // Start timer for display
            timerRef.current = setInterval(() => {
                setRecordingTime(Math.floor((Date.now() - startTimeRef.current) / 1000));
            }, 1000);

            setIsRecording(true);
            setHasRecording(false);
        } catch (err) {
            console.error("Error:", err);
            alert("Could not access camera/microphone.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            setIsRecording(false);
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        }
    };

    const handleSubmit = () => {
        if (chunksRef.current.length === 0) return;
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        // Pass both the blob and the actual duration
        const actualDuration = recordingTime || Math.floor((Date.now() - startTimeRef.current) / 1000);
        onRecordingComplete(blob, actualDuration);
    };

    const handleRetake = () => {
        setHasRecording(false);
        setRecordingTime(0);
        chunksRef.current = [];
        startRecording();
    };

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div>
            <div className="video-container">
                <video ref={videoRef} autoPlay={!hasRecording} playsInline />
                {isRecording && (
                    <>
                        <div className="recording-indicator"></div>
                        <div style={{
                            position: 'absolute',
                            top: '1rem',
                            left: '1rem',
                            background: 'rgba(0,0,0,0.6)',
                            color: 'white',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '4px',
                            fontSize: '0.875rem',
                            fontFamily: 'monospace'
                        }}>
                            {formatTime(recordingTime)}
                        </div>
                    </>
                )}
            </div>

            <div className="video-controls">
                {!isRecording && !hasRecording && (
                    <button onClick={startRecording} className="btn btn-primary">
                        🎥 Start Recording
                    </button>
                )}

                {isRecording && (
                    <button onClick={stopRecording} className="btn btn-danger">
                        ⏹ Stop ({formatTime(recordingTime)})
                    </button>
                )}

                {hasRecording && !isRecording && (
                    <>
                        <button onClick={handleRetake} className="btn btn-secondary">
                            🔄 Retake
                        </button>
                        <button onClick={handleSubmit} className="btn btn-success" disabled={isProcessing}>
                            {isProcessing ? 'Analyzing...' : `✓ Submit (${formatTime(recordingTime)})`}
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};

export default VideoRecorder;
