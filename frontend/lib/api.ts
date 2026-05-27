const API_BASE = "/api";

export async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export function importRepo(github_url: string, branch?: string) {
  return apiFetch("/repos/import", {
    method: "POST",
    body: JSON.stringify({ github_url, branch }),
  });
}

export function listRepos() {
  return apiFetch("/repos");
}

export function getRepo(id: number) {
  return apiFetch(`/repos/${id}`);
}

export function getRepoStatus(id: number) {
  return apiFetch(`/repos/${id}/status`);
}

export function getFiles(repoId: number) {
  return apiFetch(`/repos/${repoId}/files`);
}

export function getFile(repoId: number, fileId: number) {
  return apiFetch(`/repos/${repoId}/files/${fileId}`);
}

export function getTree(repoId: number) {
  return apiFetch(`/repos/${repoId}/tree`);
}

export function getSummary(repoId: number) {
  return apiFetch(`/repos/${repoId}/summary`);
}

export function getArchitecture(repoId: number) {
  return apiFetch(`/repos/${repoId}/architecture`);
}

export function getOnboarding(repoId: number) {
  return apiFetch(`/repos/${repoId}/onboarding`);
}

export function getGraph(repoId: number) {
  return apiFetch(`/repos/${repoId}/graph`);
}

export function explainFile(repoId: number, fileId: number) {
  return apiFetch(`/repos/${repoId}/files/${fileId}/explain`);
}

export function sendChat(repoId: number, message: string, history?: any[]) {
  return apiFetch(`/repos/${repoId}/chat`, {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
}

export function deleteRepo(id: number) {
  return apiFetch(`/repos/${id}`, { method: "DELETE" });
}
