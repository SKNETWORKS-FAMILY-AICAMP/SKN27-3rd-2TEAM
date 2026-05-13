const STAR_COUNT = 12;

export function StaticStarLayer() {
  return (
    <div className="static-star-layer" aria-hidden="true">
      {Array.from({ length: STAR_COUNT }, (_, index) => (
        <span key={index} className={`static-star static-star--${index + 1}`} />
      ))}
    </div>
  );
}
