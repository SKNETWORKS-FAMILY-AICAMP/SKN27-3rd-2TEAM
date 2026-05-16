import { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConstellationHome } from "./components/home/ConstellationHome";
import { MainRecommendationPage } from "./pages/MainRecommendationPage";
import { ChatbotPage } from "./pages/ChatbotPage";
import { MusicDetailPage } from "./pages/MusicDetailPage";
import { NotFoundPage } from "./pages/NotFoundPage";
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

type Page = "home" | "main" | "personalized" | "discovery" | "newRelease" | "chatbot" | "musicDetail" | "notFound";

function pageFromLocation(): Page {
  const path = window.location.pathname;
  const detailContentId = new URLSearchParams(window.location.search).get("detail");
  if (path === "/") return "home";
  if (path === "/recommendations") return "main";
  if (path === "/recommendations/personalized") return "personalized";
  if (path === "/recommendations/discovery") return "discovery";
  if (path === "/recommendations/new-release") return "newRelease";
  if (path === "/chatbot") return "chatbot";
  if (path === "/music" && detailContentId) return "musicDetail";
  if (path === "/music") return "musicDetail";
  return "notFound";
}

function pathForPage(page: Page): string {
  if (page === "main") return "/recommendations";
  if (page === "personalized") return "/recommendations/personalized";
  if (page === "discovery") return "/recommendations/discovery";
  if (page === "newRelease") return "/recommendations/new-release";
  if (page === "chatbot") return "/chatbot";
  if (page === "musicDetail") return "/music";
  return "/";
}

function AppContent() {
  const [page, setPage] = useState<Page>(() => pageFromLocation());
  const { userId, setUserId } = useSessionStore();
  const { theme, toggle } = useThemeStore();

  useEffect(() => {
    const syncPage = () => setPage(pageFromLocation());
    window.addEventListener("popstate", syncPage);
    return () => window.removeEventListener("popstate", syncPage);
  }, []);

  const navigate = (nextPage: Page) => {
    window.history.pushState({}, "", pathForPage(nextPage));
    setPage(nextPage);
  };

  return (
    <div className="app">
      {page !== "home" && (
        <nav className="app-nav">
          <button className="nav-brand" type="button" onClick={() => navigate("home")}>
            RIMAS
          </button>
          <button
            className="nav-btn"
            onClick={() => {
              navigate("home");
            }}
          >
            홈
          </button>
          <button
            className={`nav-btn${page === "chatbot" ? " nav-btn--active" : ""}`}
            onClick={() => {
              navigate("chatbot");
            }}
          >
            DJ 챗봇
          </button>
          <button className="theme-toggle" onClick={toggle} aria-label="테마 전환">
            {theme === "dark" ? "☀" : "☾"}
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
          <ConstellationHome onNavigate={navigate} />
        )}
        {page === "main" && (
          <MainRecommendationPage
            onChatOpen={() => navigate("chatbot")}
          />
        )}
        {page === "personalized" && (
          <MainRecommendationPage
            category="personalized"
            onChatOpen={() => navigate("chatbot")}
          />
        )}
        {page === "discovery" && (
          <MainRecommendationPage
            category="discovery"
            onChatOpen={() => navigate("chatbot")}
          />
        )}
        {page === "newRelease" && (
          <MainRecommendationPage
            category="newRelease"
            onChatOpen={() => navigate("chatbot")}
          />
        )}
        {page === "musicDetail" && (
          <MusicDetailPage onChatOpen={() => navigate("chatbot")} />
        )}
        {page === "chatbot" && <ChatbotPage onNavigateHome={() => navigate("home")} />}
        {page === "notFound" && <NotFoundPage onNavigateHome={() => navigate("home")} />}
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
