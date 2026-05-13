import { Home } from "../../pages/Home";

export type RecommendationCategoryTarget = "personalized" | "discovery" | "newRelease";
export type HomePageTarget = RecommendationCategoryTarget | "chatbot";

type Props = {
  onNavigate: (page: HomePageTarget) => void;
};

export function ConstellationHome({ onNavigate }: Props) {
  return <Home onNavigate={onNavigate} />;
}
