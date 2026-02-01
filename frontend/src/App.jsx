
import React, { useState, Component } from 'react';
import './index.css';
import SetupForm from './components/SetupForm';
import InterviewSession from './components/InterviewSession';

// Error Boundary to catch any crashes
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h2 style={{ color: '#ef4444' }}>Something went wrong</h2>
          <p style={{ color: '#666' }}>{this.state.error?.message || 'Unknown error'}</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              padding: '0.75rem 1.5rem',
              background: '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Reload App
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [sessionData, setSessionData] = useState(null);

  const handleSetupComplete = (data) => {
    console.log('Session started:', data);
    setSessionData(data);
  };

  const handleInterviewExit = () => {
    setSessionData(null);
  };

  return (
    <ErrorBoundary>
      <div className="app-container">
        <header className="header">
          <div className="logo">
            <div className="logo-icon"></div>
            <span>CloseIt</span>
          </div>
        </header>

        <main className="main-content">
          {!sessionData ? (
            <div className="fade-in">
              <div className="hero">
                <h1 className="hero-title">Ace Your Interview</h1>
                <p className="hero-subtitle">
                  Practice with AI-powered mock interviews. Get instant feedback.
                </p>
              </div>
              <SetupForm onComplete={handleSetupComplete} />
            </div>
          ) : (
            <ErrorBoundary>
              <InterviewSession
                sessionId={sessionData.session_id}
                questions={sessionData.questions || []}
                onExit={handleInterviewExit}
              />
            </ErrorBoundary>
          )}
        </main>
      </div>
    </ErrorBoundary>
  );
}

export default App;
