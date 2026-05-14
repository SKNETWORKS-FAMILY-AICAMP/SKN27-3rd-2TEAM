import { memo, useState } from "react";
import type { ChatDisplayRecommendation } from "../../types";

interface Props {
  cards: ChatDisplayRecommendation[];
  onAddToTaste?: (contentId: string) => Promise<void>;
}

export const RelatedRecommendationCards = memo(function RelatedRecommendationCards({ cards, onAddToTaste }: Props) {
  const [savingId, setSavingId] = useState<string | null>(null);
  const [addedIds, setAddedIds] = useState<Set<string>>(new Set());

  if (!cards || cards.length === 0) return null;

  const handleAddToTaste = async (contentId: string) => {
    if (addedIds.has(contentId) || savingId) return;
    setSavingId(contentId);
    try {
      await onAddToTaste?.(contentId);
      setAddedIds((prev) => new Set(prev).add(contentId));
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="related-cards">
      <p className="related-cards__title">관련 추천</p>
      <div className="related-cards__list">
        {cards.map((card) => {
          const isAdded = addedIds.has(card.content_id);
          const isSaving = savingId === card.content_id;
          const label = isAdded ? "취향에 추가됨" : isSaving ? "추가 중..." : "내 취향에 추가";
          return (
            <div key={card.content_id} className="related-card">
              <span className="related-card__label">{card.label ?? card.recommendation_category}</span>
              <span className="related-card__title">{card.title}</span>
              <span className="related-card__artist">{card.artist}</span>
              <p className="related-card__reason">{card.display_reason}</p>
              {onAddToTaste && (
                <button
                  className="related-card__taste-btn"
                  type="button"
                  onClick={() => handleAddToTaste(card.content_id)}
                  disabled={isAdded || isSaving}
                >
                  {label}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});
