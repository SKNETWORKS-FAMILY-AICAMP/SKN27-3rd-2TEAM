import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConstellationHome } from "./components/home/ConstellationHome";
import type { RecommendationCategoryTarget } from "./components/home/ConstellationHome";
import { MainRecommendationPage } from "./pages/MainRecommendationPage";
import { ChatbotPage } from "./pages/ChatbotPage";
import { useSessionStore } from "./stores/sessionStore";
import { useThemeStore } from "./stores/themeStore";
import "./App.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type Page = "home" | "main" | "chatbot";

function AppContent() {
  const [page, setPage] = useState<Page>("home");
  const [recommendationCategory, setRecommendationCategory] =
    useState<RecommendationCategoryTarget | undefined>();
  const { userId, setUserId } = useSessionStore();
  const { theme, toggle } = useThemeStore();

  return (
    <div className="app">
      {page !== "home" && (
        <nav className="app-nav">
          <button className="nav-brand" type="button" onClick={() => setPage("home")}>
            RIMAS
          </button>
          <button
            className={`nav-btn${page === "main" ? " nav-btn--active" : ""}`}
            onClick={() => {
              setRecommendationCategory(undefined);
              setPage("main");
            }}
          >
            추천
          </button>
          <button
            className={`nav-btn${page === "chatbot" ? " nav-btn--active" : ""}`}
            onClick={() => {
              setRecommendationCategory(undefined);
              setPage("chatbot");
            }}
          >
            DJ 챗봇
          </button>
          <button className="theme-toggle" onClick={toggle} aria-label="테마 전환">
            {theme === "dark" ? "☾" : "☀"}
          </button>
          <select
            className="user-select"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          >
            {["user_001", "user_002", "user_003"].map((id) => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        </nav>
      )}

      <main className="app-content">
        {page === "home" && (
          <ConstellationHome
            onNavigate={(nextPage, category) => {
              setRecommendationCategory(category);
              setPage(nextPage);
            }}
          />
        )}
        {page === "main" && (
          <MainRecommendationPage
            initialCategory={recommendationCategory}
            onChatOpen={() => {
              setRecommendationCategory(undefined);
              setPage("chatbot");
            }}
          />
        )}
        {page === "chatbot" && <ChatbotPage />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
