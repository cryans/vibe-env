export interface SessionListResponse {
  filename: string;
  id: string;
  timestamp: string;
  cwd: string;
}

export interface SessionDetailResponse {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  session: any[];
}
