import type { MusicDetail } from "../../types";
import { DreamButton } from "../ui/DreamButton";
import { GlassPanel } from "../ui/GlassPanel";

interface Props {
  detail?: MusicDetail;
  isLoading: boolean;
  isError: boolean;
  onClose: () => void;
  onAddToTaste?: (contentId: string) => Promise<void>;
  isTasteSaving?: boolean;
  isTasteAdded?: boolean;
}

export function MusicDetailModal({ detail, isLoading, isError, onClose, onAddToTaste, isTasteSaving, isTasteAdded }: Props) {
  const title = detail?.title?.trim() || "제목 정보가 없습니다";
  const artist = detail?.artist?.trim() || "아티스트 정보가 없습니다";
  const reason = detail?.display_reason?.trim() || "추천 사유가 제공되지 않았습니다.";
  const evidenceSummary = detail ? detail.evidence_summary.trim() : "";
  const sourceLabel = formatSourceLabel(detail ? detail.source : undefined);

  const tasteButtonLabel = isTasteAdded ? "취향에 추가됨" : isTasteSaving ? "추가 중..." : "내 취향에 추가";

  return (
    <div className="detail-modal" role="dialog" aria-modal="true" aria-labelledby="music-detail-title">
      <button className="detail-modal__backdrop" type="button" aria-label="Close detail" onClick={onClose} />
      <GlassPanel className="detail-modal__panel" intensity="strong">
        <DreamButton className="detail-modal__close" onClick={onClose}>
          x
        </DreamButton>

        {isLoading && <div className="detail-modal__state">상세 정보를 불러오는 중입니다...</div>}
        {isError && <div className="detail-modal__state detail-modal__state--error">상세 정보를 불러오지 못했습니다.</div>}

        {!isLoading && !isError && detail && (
          <>
            <div className="detail-modal__cover">♪</div>
            <div className="detail-modal__body">
              <h2 id="music-detail-title" className="detail-modal__title">{title}</h2>
              <p className="detail-modal__artist">{artist}</p>
              {detail.album && <p className="detail-modal__album">{detail.album}</p>}

              <div className="detail-modal__tags">
                {detail.genre.map((genre) => (
                  <span key={genre} className="tag tag--genre">{genre}</span>
                ))}
                {detail.mood.map((mood) => (
                  <span key={mood} className="tag tag--mood">{mood}</span>
                ))}
              </div>

              <section className="detail-modal__section">
                <h3>추천 이유</h3>
                <p>{reason}</p>
              </section>

              <section className="detail-modal__section detail-modal__section--evidence">
                <h3>큐레이션 근거</h3>
                <dl className="detail-modal__evidence">
                  <div>
                    <dt>근거 출처</dt>
                    <dd>{sourceLabel}</dd>
                  </div>
                  {evidenceSummary && (
                    <div>
                      <dt>검색 근거 요약</dt>
                      <dd>{evidenceSummary}</dd>
                    </div>
                  )}
                </dl>
              </section>

              {onAddToTaste && (
                <DreamButton
                  className="detail-modal__taste-btn"
                  onClick={() => onAddToTaste(detail.content_id)}
                  disabled={isTasteSaving || isTasteAdded}
                >
                  {tasteButtonLabel}
                </DreamButton>
              )}
            </div>
          </>
        )}
      </GlassPanel>
    </div>
  );
}

function formatSourceLabel(source?: string) {
  if (source === "rag_state") {
    return "RAG 근거 기반";
  }
  if (source === "music_catalog") {
    return "음악 카탈로그 기반";
  }
  return "확인된 상세 모델 기반";
}
