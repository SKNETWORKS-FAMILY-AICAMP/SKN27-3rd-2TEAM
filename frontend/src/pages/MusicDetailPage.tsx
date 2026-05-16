import { MainRecommendationPage } from "./MainRecommendationPage";

interface Props {
  onChatOpen?: () => void;
}

export function MusicDetailPage({ onChatOpen }: Props) {
  return <MainRecommendationPage onChatOpen={onChatOpen} />;
}
