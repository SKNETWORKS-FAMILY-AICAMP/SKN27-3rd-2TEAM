import { MascotCharacter } from "../mascot/MascotCharacter";

export type RecommendationCategoryTarget = "personalized" | "discovery" | "newRelease";
export type HomePageTarget = RecommendationCategoryTarget | "chatbot";

type ConstellationNode = {
  id: string;
  label: string;
  x: number;
  y: number;
  target: HomePageTarget;
};

const constellationNodes: ConstellationNode[] = [
  { id: "personalized", label: "개인화 추천", target: "personalized", x: 28, y: 36 },
  { id: "discovery", label: "새로운 취향", target: "discovery", x: 72, y: 36 },
  { id: "newRelease", label: "신규 발매", target: "newRelease", x: 30, y: 68 },
  { id: "chatbot", label: "DJ 챗봇", target: "chatbot", x: 70, y: 68 },
];

const constellationLines = [
  ["personalized", "discovery"],
  ["discovery", "chatbot"],
  ["chatbot", "newRelease"],
  ["newRelease", "personalized"],
  ["personalized", "chatbot"],
  ["discovery", "newRelease"],
] as const;

type Props = {
  onNavigate: (page: HomePageTarget) => void;
};

function findNode(id: string) {
  return constellationNodes.find((node) => node.id === id);
}

export function ConstellationHome({ onNavigate }: Props) {
  return (
    <section className="constellation-home" aria-label="RIMAS 추천 카테고리 홈">
      <div className="constellation-background" aria-hidden="true" />

      <svg className="constellation-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        {constellationLines.map(([fromId, toId]) => {
          const from = findNode(fromId);
          const to = findNode(toId);
          if (!from || !to) return null;

          return (
            <line
              key={`${fromId}-${toId}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              className="constellation-line"
            />
          );
        })}
      </svg>

      <div className="constellation-center" aria-hidden="true">
        <MascotCharacter state="idle" />
        <span className="constellation-brand">RIMAS</span>
      </div>

      <nav className="constellation-nav" aria-label="추천 카테고리">
        {constellationNodes.map((node) => (
          <button
            key={node.id}
            type="button"
            className="constellation-node"
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
            onClick={() => onNavigate(node.target)}
          >
            <span className="constellation-star" aria-hidden="true" />
            <span className="constellation-label">{node.label}</span>
          </button>
        ))}
      </nav>
    </section>
  );
}
