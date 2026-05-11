import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchMusicDetail } from "../api/musicDetailApi";
import { fetchMainRecommendations } from "../api/recommendation";
import { DreamBackground } from "../components/background/DreamBackground";
import { CharacterDjBanner } from "../components/recommendation/CharacterDjBanner";
import { MusicDetailModal } from "../components/recommendation/MusicDetailModal";
import { RecommendationSection } from "../components/recommendation/RecommendationSection";
import { TopTasteHeader } from "../components/recommendation/TopTasteHeader";
import { useRequestId, useRequestIdPerKey } from "../hooks/useRequestId";
import { useSessionStore } from "../stores/sessionStore";
import type { RecommendationCategoryTarget } from "../components/home/ConstellationHome";

interface Props {
  onChatOpen?: () => void;
  initialCategory?: RecommendationCategoryTarget;
}

export function MainRecommendationPage({ onChatOpen, initialCategory }: Props) {
  const { userId, sessionId } = useSessionStore();
  const [detailContentId, setDetailContentId] = useState(() => {
    return new URLSearchParams(window.location.search).get("detail");
  });

  // API 호출 흐름과 React Query key는 기존 계약을 그대로 유지한다.
  const mainRequestId = useRequestId();
  const detailRequestId = useRequestIdPerKey(detailContentId);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["main-recommendations", userId, sessionId],
    queryFn: () => fetchMainRecommendations(userId, sessionId, mainRequestId),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
  const detailQuery = useQuery({
    queryKey: ["music-detail", detailContentId],
    queryFn: () =>
      fetchMusicDetail(detailContentId ?? "", {
        userId,
        sessionId,
        requestId: detailRequestId,
      }),
    enabled: Boolean(detailContentId),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  useEffect(() => {
    const syncFromLocation = () => {
      setDetailContentId(new URLSearchParams(window.location.search).get("detail"));
    };
    window.addEventListener("popstate", syncFromLocation);
    return () => window.removeEventListener("popstate", syncFromLocation);
  }, []);

  const openDetail = (contentId: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set("detail", contentId);
    window.history.pushState({}, "", url);
    setDetailContentId(contentId);
  };

  const closeDetail = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("detail");
    window.history.pushState({}, "", `${url.pathname}${url.search}`);
    setDetailContentId(null);
  };

  useEffect(() => {
    if (!data || !initialCategory) return;

    const section = document.getElementById(`recommendation-${initialCategory}`);
    section?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [initialCategory, data]);

  if (isLoading) {
    return (
      <DreamBackground variant="main">
        <div className="page-loading">추천을 불러오는 중입니다...</div>
      </DreamBackground>
    );
  }

  if (isError || !data) {
    return (
      <DreamBackground variant="main">
        <div className="page-error">추천을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</div>
      </DreamBackground>
    );
  }

  const vm = data.view_model;

  return (
    <DreamBackground variant="main">
      <div className="main-page">
        {data.session_degraded && (
          <div className="session-degraded-banner">
            세션 연결이 불안정하여 개인화 기능이 일부 제한될 수 있습니다.
          </div>
        )}

        <TopTasteHeader tasteBadges={vm.taste_badges} todayTheme={vm.today_theme} />

        <section className="hero-section">
          <CharacterDjBanner message={vm.character_message} onChatOpen={onChatOpen} />
        </section>

        <div className="recommendation-dashboard">
          <div id="recommendation-personalized">
            <RecommendationSection
              title="개인화 추천"
              label="Taste Based"
              cards={vm.personalized}
              onOpenDetail={openDetail}
            />
          </div>
          <div id="recommendation-discovery">
            <RecommendationSection
              title="새로운 취향"
              label="Discovery"
              cards={vm.discovery}
              onOpenDetail={openDetail}
            />
          </div>
          <div id="recommendation-newRelease">
            <RecommendationSection
              title="신규 발매"
              label="New Release"
              cards={vm.new_release}
              onOpenDetail={openDetail}
            />
          </div>
        </div>

        {vm.personalized_guide && (
          <p className="personalized-guide">{vm.personalized_guide}</p>
        )}

        {detailContentId && (
          <MusicDetailModal
            detail={detailQuery.data?.music_detail}
            isLoading={detailQuery.isLoading}
            isError={detailQuery.isError}
            onClose={closeDetail}
          />
        )}
      </div>
    </DreamBackground>
  );
}
