import type { MusicDetail } from "../../types";

interface Props {
  detail?: MusicDetail;
  isLoading: boolean;
  isError: boolean;
  onClose: () => void;
}

export function MusicDetailModal({ detail, isLoading, isError, onClose }: Props) {
  return (
    <div className="detail-modal" role="dialog" aria-modal="true" aria-labelledby="music-detail-title">
      <button className="detail-modal__backdrop" type="button" aria-label="Close detail" onClick={onClose} />
      <section className="detail-modal__panel">
        <button className="detail-modal__close" type="button" onClick={onClose} aria-label="Close detail">
          x
        </button>

        {isLoading && <div className="detail-modal__state">Loading detail...</div>}
        {isError && <div className="detail-modal__state detail-modal__state--error">Failed to load detail.</div>}

        {!isLoading && !isError && detail && (
          <>
            <div className="detail-modal__cover">note</div>
            <div className="detail-modal__body">
              <span className="detail-modal__source">{detail.source}</span>
              <h2 id="music-detail-title" className="detail-modal__title">{detail.title}</h2>
              <p className="detail-modal__artist">{detail.artist}</p>
              {detail.album && <p className="detail-modal__album">{detail.album}</p>}

              <div className="detail-modal__tags">
                {detail.genre.map((genre) => (
                  <span key={genre} className="tag tag--genre">{genre}</span>
                ))}
                {detail.mood.map((mood) => (
                  <span key={mood} className="tag tag--mood">{mood}</span>
                ))}
              </div>

              {detail.display_reason && (
                <section className="detail-modal__section">
                  <h3>Recommendation Reason</h3>
                  <p>{detail.display_reason}</p>
                </section>
              )}

              {detail.evidence_summary && detail.evidence_summary !== detail.display_reason && (
                <section className="detail-modal__section">
                  <h3>Evidence Summary</h3>
                  <p>{detail.evidence_summary}</p>
                </section>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
