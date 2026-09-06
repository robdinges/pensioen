import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./planner-ui.css";

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <main style={{ maxWidth: 760, margin: "3rem auto", padding: "1.5rem" }}>
          <h1>De interface kon niet worden geladen</h1>
          <p>{this.state.error.message}</p>
          <button
            type="button"
            onClick={() => {
              localStorage.removeItem("pensioen-ui-session-v1");
              window.location.reload();
            }}
          >
            Wis oude sessie en herlaad
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
);
