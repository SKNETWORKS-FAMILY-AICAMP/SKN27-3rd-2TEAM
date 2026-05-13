import { memo } from "react";
import type { RecommendationCard as CardType } from "../../types";
import { GlassPanel } from "../ui/GlassPanel";
import { RecommendationCard } from "./RecommendationCard";

interface Props {
  title: string;
  label?: string;
  cards: CardType[];
  onOpenDetail?: (contentId: string) => void;
}

export const RecommendationSection = memo(function RecommendationSection({
  title,
  label,
  cards,
  onOpenDetail,
}: Props) {
  if (!cards || cards.length === 0) return null;

  return (
    <GlassPanel className="rec-section" intensity="base">
      <div className="rec-section__header">
        {label && <span className="rec-section__label">{label}</span>}
        <h2 className="rec-section__title">{title}</h2>
      </div>
      <div className="rec-section__grid">
        {cards.map((card) => (
          <RecommendationCard key={card.content_id} card={card} onOpenDetail={onOpenDetail} />
        ))}
      </div>
    </GlassPanel>
  );
});
