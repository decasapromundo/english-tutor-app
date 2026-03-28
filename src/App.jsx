import { useState } from "react";
import WelcomeScreen from "./components/WelcomeScreen";
import ChatInterface from "./components/ChatInterface";

export default function App() {
  const [started, setStarted] = useState(false);
  const [initialMessage, setInitialMessage] = useState(null);

  function handleStart() {
    setInitialMessage("começar");
    setStarted(true);
  }

  return (
    <div className="app">
      <header className="app-header">
        <span className="header-logo">🚢</span>
        <span className="header-title">English Tutor — Cruzeiros</span>
        {started && (
          <button className="btn-reset" onClick={() => { setStarted(false); setInitialMessage(null); }}>
            Nova sessão
          </button>
        )}
      </header>

      <main className="app-main">
        {!started ? (
          <WelcomeScreen onStart={handleStart} />
        ) : (
          <ChatInterface initialMessage={initialMessage} />
        )}
      </main>
    </div>
  );
}
