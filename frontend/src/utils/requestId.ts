export function generateRequestId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `req_${crypto.randomUUID().replace(/-/g, "")}`;
  }
  // fallback for environments without crypto.randomUUID
  return `req_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}
