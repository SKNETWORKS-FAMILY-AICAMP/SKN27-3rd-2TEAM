import { memo } from "react";
import type { RecommendationCard as CardType } from "../../types";

interface Props {
  card: CardType;
  onOpenDetail?: (contentId: string) => void;
}

export const RecommendationCard = memo(function RecommendationCard({ card, onOpenDetail }: Props) {
  return (
    <button
      className="rec-card"
      type="button"
      onClick={() => onOpenDetail?.(card.content_id)}
      aria-label={`${card.title} detail`}
    >
      <div className="rec-card__cover">note</div>

      {card.label && (
        <span className="rec-card__label">{card.label}</span>
      )}

      <div className="rec-card__title">{card.title}</div>
      <div className="rec-card__artist">{card.artist}</div>

      {(card.genre?.length || card.mood?.length) ? (
        <div className="rec-card__tags">
          {card.genre?.map((genre) => (
            <span key={genre} className="tag tag--genre">{genre}</span>
          ))}
          {card.mood?.map((mood) => (
            <span key={mood} className="tag tag--mood">{mood}</span>
          ))}
        </div>
      ) : null}

      {card.display_reason && (
        <p className="rec-card__reason">{card.display_reason}</p>
      )}
    </button>
  );
});
