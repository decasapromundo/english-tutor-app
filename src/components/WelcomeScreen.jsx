export default function WelcomeScreen({ onStart }) {
  return (
    <div className="welcome">
      <div className="welcome-card">
        <div className="welcome-icon">🚢</div>
        <h1>English Tutor</h1>
        <p className="welcome-subtitle">Para trabalhadores de cruzeiro</p>
        <p className="welcome-desc">
          Aprenda inglês no seu ritmo com um tutor personalizado.
          Vamos descobrir seu nível e criar um plano de estudos da semana.
        </p>
        <div className="cefr-levels">
          <span className="level a1a2">A1/A2</span>
          <span className="arrow">→</span>
          <span className="level b1b2">B1/B2</span>
          <span className="arrow">→</span>
          <span className="level c1c2">C1/C2</span>
        </div>
        <button className="btn-primary" onClick={onStart}>
          Começar agora
        </button>
        <p className="welcome-hint">
          Digite <strong>"começar"</strong> para iniciar o teste de nivelamento
        </p>
      </div>
    </div>
  );
}
