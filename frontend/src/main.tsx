import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AppRouter } from "./router";
import { ThemeProvider } from "./context/ThemeContext";
import { LanguageProvider } from "./context/LanguageContext";
// Initialize i18next (single source of truth for the active language).
import "./i18n";
import "./styles/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <LanguageProvider>
      <ThemeProvider>
        <AppRouter />
      </ThemeProvider>
    </LanguageProvider>
  </StrictMode>,
);
