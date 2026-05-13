const GLOW_COUNT = 3;

export function SoftGlowLayer() {
  return (
    <div className="soft-glow-layer" aria-hidden="true">
      {Array.from({ length: GLOW_COUNT }, (_, index) => (
        <span key={index} className={`soft-glow soft-glow--${index + 1}`} />
      ))}
    </div>
  );
}
