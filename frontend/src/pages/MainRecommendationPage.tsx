import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchMusicDetail } from "../api/musicDetailApi";
import { fetchMainRecommendations } from "../api/recommendation";
import { CharacterDjBanner } from "../components/recommendation/CharacterDjBanner";
import { MusicDetailModal } from "../components/recommendation/MusicDetailModal";
import { RecommendationSection } from "../components/recommendation/RecommendationSection";
import { TopTasteHeader } from "../components/recommendation/TopTasteHeader";
import { useRequestId, useRequestIdPerKey } from "../hooks/useRequestId";
import { useSessionStore } from "../stores/sessionStore";

interface Props {
  onChatOpen?: () => void;
}

export function MainRecommendationPage({ onChatOpen }: Props) {
  const { userId, sessionId } = useSessionStore();
  const [detailContentId, setDetailContentId] = useState(() => {
    return new URLSearchParams(window.location.search).get("detail");
  });

  // 메인 추천: 마운트 수명 동안 동일 requestId 유지 → retry 시 백엔드 중복 차단 연동
  const mainRequestId = useRequestId();
  // 음악 상세: content_id가 바뀔 때마다 새 requestId 생성
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

  if (isLoading) {
    return <div className="page-loading">추천을 불러오는 중...</div>;
  }

  if (isError || !data) {
    return <div className="page-error">추천을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</div>;
  }

  const vm = data.view_model;

  return (
    <div className="main-page">
      {data.session_degraded && (
        <div className="session-degraded-banner">
          세션 서버와 연결이 원활하지 않아 개인화 기능이 일부 제한될 수 있습니다.
        </div>
      )}
      <TopTasteHeader tasteBadges={vm.taste_badges} todayTheme={vm.today_theme} />
      <CharacterDjBanner message={vm.character_message} onChatOpen={onChatOpen} />

      <RecommendationSection
        title="개인화 추천"
        label="취향 기반"
        cards={vm.personalized}
        onOpenDetail={openDetail}
      />
      <RecommendationSection
        title="새로운 취향 탐색"
        label="Discovery"
        cards={vm.discovery}
        onOpenDetail={openDetail}
      />
      <RecommendationSection
        title="신규 발매"
        label="New Release"
        cards={vm.new_release}
        onOpenDetail={openDetail}
      />

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
  );
}
