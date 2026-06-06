export const SESSION_REQUEST_LIMIT = 15;

export function getRemainingRequests(used: number): number {
  return Math.max(0, SESSION_REQUEST_LIMIT - used);
}

export function isSessionExhausted(used: number): boolean {
  return used >= SESSION_REQUEST_LIMIT;
}
