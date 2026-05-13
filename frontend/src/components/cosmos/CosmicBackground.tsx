import { memo, type ReactNode } from "react";
import { FloatingParticles } from "./FloatingParticles";
import { StarField } from "./StarField";

type Props = {
  children: ReactNode;
};

export const CosmicBackground = memo(function CosmicBackground({ children }: Props) {
  return (
    <section className="relative min-h-screen overflow-hidden bg-[#12002b] text-white">
      <div
        className="absolute inset-0 z-0 bg-[url('/img/background.png')] bg-cover bg-center bg-no-repeat"
        aria-hidden="true"
      />
      <div
        className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_50%_48%,rgba(18,0,43,0.08),transparent_34%),linear-gradient(180deg,rgba(9,5,32,0.16)_0%,rgba(18,0,43,0.28)_58%,rgba(18,0,43,0.42)_100%)]"
        aria-hidden="true"
      />
      <div className="absolute left-[-14%] top-[18%] z-0 h-[34rem] w-[34rem] rounded-full bg-violet-500/20 blur-[130px]" aria-hidden="true" />
      <div className="absolute right-[-12%] top-[10%] z-0 h-[30rem] w-[30rem] rounded-full bg-blue-500/14 blur-[130px]" aria-hidden="true" />
      <div className="absolute bottom-[-24%] left-[20%] z-0 h-[38rem] w-[58rem] rounded-full bg-fuchsia-300/12 blur-[120px]" aria-hidden="true" />
      <StarField />
      <FloatingParticles />
      <div className="pointer-events-none absolute inset-x-[-8%] bottom-[-18%] z-[3] h-[34%] bg-[radial-gradient(ellipse_at_12%_82%,rgba(93,58,142,0.78),transparent_34%),radial-gradient(ellipse_at_32%_76%,rgba(151,86,178,0.62),transparent_32%),radial-gradient(ellipse_at_58%_86%,rgba(64,45,120,0.72),transparent_36%),radial-gradient(ellipse_at_82%_75%,rgba(157,91,185,0.54),transparent_34%)] blur-[10px]" aria-hidden="true" />
      <div className="relative z-[5] min-h-screen">{children}</div>
    </section>
  );
});
