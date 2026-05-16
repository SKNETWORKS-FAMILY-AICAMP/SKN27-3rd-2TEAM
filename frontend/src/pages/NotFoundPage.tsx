import { DreamBackground } from "../components/background/DreamBackground";
import { DreamButton } from "../components/ui/DreamButton";

interface Props {
  onNavigateHome?: () => void;
}

export function NotFoundPage({ onNavigateHome }: Props) {
  return (
    <DreamBackground variant="main">
      <div className="page-error">
        <p>요청한 화면을 찾을 수 없습니다.</p>
        <DreamButton onClick={onNavigateHome}>홈으로 이동</DreamButton>
      </div>
    </DreamBackground>
  );
}
