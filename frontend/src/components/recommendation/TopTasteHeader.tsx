import { memo } from "react";

interface Props {
  tasteBadges: string[];
  todayTheme: string;
}

export const TopTasteHeader = memo(function TopTasteHeader({ tasteBadges, todayTheme }: Props) {
  return (
    <header className="taste-header">
      <div className="taste-header__badges">
        {tasteBadges.map((badge) => (
          <span key={badge} className="badge">{badge}</span>
        ))}
      </div>
      {todayTheme && <p className="taste-header__theme">{todayTheme}</p>}
    </header>
  );
});
