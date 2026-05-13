import { memo } from "react";
import { CenterMascotOrb } from "../components/cosmos/CenterMascotOrb";
import { ConstellationLines } from "../components/cosmos/ConstellationLines";
import { CosmicBackground } from "../components/cosmos/CosmicBackground";
import { OrbitNode, type OrbitFeature } from "../components/cosmos/OrbitNode";
import type { HomePageTarget } from "../components/home/ConstellationHome";

const orbitFeatures: OrbitFeature[] = [
  {
    id: "recommend",
    title: "개인화 추천",
    position: "left-top",
    imageSrc: "/img/icon1.png",
    target: "personalized",
    x: 22,
    y: 28,
    controlX: 36,
    controlY: 36,
  },
  {
    id: "discovery",
    title: "새로운 취향",
    position: "right-top",
    imageSrc: "/img/icon2.png",
    target: "discovery",
    x: 78,
    y: 30,
    controlX: 64,
    controlY: 35,
  },
  {
    id: "new-release",
    title: "신규 발매",
    position: "left-bottom",
    imageSrc: "/img/icon3.png",
    target: "newRelease",
    x: 23,
    y: 70,
    controlX: 36,
    controlY: 63,
  },
  {
    id: "chatbot",
    title: "DJ 챗봇",
    position: "right-bottom",
    imageSrc: "/img/icon4.png",
    target: "chatbot",
    x: 76,
    y: 68,
    controlX: 64,
    controlY: 62,
  },
];

type Props = {
  onNavigate: (page: HomePageTarget) => void;
};

export const Home = memo(function Home({ onNavigate }: Props) {
  return (
    <CosmicBackground>
      <div className="relative mx-auto min-h-screen w-full max-w-[110rem] px-6 max-md:flex max-md:flex-col max-md:items-center max-md:gap-8 max-md:py-12">
        <div className="hidden max-md:block">
          <CenterMascotOrb layout="mobile" />
        </div>

        <div className="absolute inset-0 max-md:hidden">
          <ConstellationLines points={orbitFeatures} />
          <CenterMascotOrb />
          {orbitFeatures.map((feature) => (
            <OrbitNode key={feature.id} feature={feature} onSelect={onNavigate} />
          ))}
        </div>

        <div className="hidden w-full max-w-md grid-cols-2 gap-x-5 gap-y-7 pt-2 max-md:grid">
          {orbitFeatures.map((feature) => (
            <OrbitNode key={feature.id} feature={feature} onSelect={onNavigate} />
          ))}
        </div>
      </div>
    </CosmicBackground>
  );
});
