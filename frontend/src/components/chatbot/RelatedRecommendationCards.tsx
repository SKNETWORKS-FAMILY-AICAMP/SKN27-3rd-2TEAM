import { memo } from "react";
import type { ChatDisplayRecommendation } from "../../types";

interface Props {
  cards: ChatDisplayRecommendation[];
}

export const RelatedRecommendationCards = memo(function RelatedRecommendationCards({ cards }: Props) {
  if (!cards || cards.length === 0) return null;

  return (
    <div className="related-cards">
      <p className="related-cards__title">관련 추천</p>
      <div className="related-cards__list">
        {cards.map((card) => (
          <div key={card.content_id} className="related-card">
            <span className="related-card__label">{card.label ?? card.recommendation_category}</span>
            <span className="related-card__title">{card.title}</span>
            <span className="related-card__artist">{card.artist}</span>
            <p className="related-card__reason">{card.display_reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
});
