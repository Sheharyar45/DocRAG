import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import supabase from "./supabaseClient";

const BASE_URL = "http://localhost:8000";

export type NoteType = {
  id: string;
  title: string;
  content: string;
  user_id: string;
  is_starred: boolean;
  is_pinned: boolean;
  is_trashed: boolean;
  folder_id: string | null;
  folder?: string | null;
  created_at: string;
  updated_at: string;
  tags?: string[];
};

export type NoteCreateType = {
  title: string;
  content: string;
  user_id: string;
};

export type NoteUpdateType = Partial<{
  title: string;
  content: string;
  is_starred: boolean;
  is_pinned: boolean;
  is_trashed: boolean;
  folder_id: string | null;
}>;

export type FolderType = {
  id: string;
  name: string;
  user_id: string;
  created_at: string;
  updated_at: string;
};

export type FolderCreateType = {
  name: string;
};

export type FolderUpdateType = {
  name?: string;
};

// ── Chat types ──────────────────────────────────────────────────

export type ChatMessageType = {
  role: "user" | "assistant";
  content: string;
};

export type SourceCitationType = {
  note_id: string;
  title: string;
  snippet: string;
  score: number;
};

export type ChatResponseType = {
  answer: string;
  sources: SourceCitationType[];
  search_mode: string;
  chunks_retrieved: number;
  cache_hit: boolean;
};

export type ChatRequestType = {
  query: string;
  folder_id?: string | null;
  search_mode?: string;
  top_k?: number;
  conversation_history?: ChatMessageType[];
};

async function authorizedFetch(input: RequestInfo, init: RequestInit = {}) {
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;

  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const res = await fetch(input, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.message || "Request failed");
  }
  return res.json();
}

export function useNotes(userId: string | null) {
  return useQuery({
    queryKey: ["notes", userId],
    queryFn: () => authorizedFetch(`${BASE_URL}/api/notes/`),
    staleTime: 0,
    refetchOnWindowFocus: false,
    select: (data) => data as NoteType[],
  });
}

export function useNoteById(noteId: string | null, userId: string | null) {
  return useQuery({
    queryKey: ["notes", noteId, userId],
    queryFn: () =>
      authorizedFetch(`${BASE_URL}/api/notes/${noteId}`),
    enabled: !!noteId,
    staleTime: 30_000,
    select: (data) => data as NoteType,
  });
}

export function useCreateNote(userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (newNote: NoteCreateType) =>
      authorizedFetch(`${BASE_URL}/api/notes/`, {
        method: "POST",
        body: JSON.stringify(newNote),
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["notes", userId] });
    },
  });
}

export function useUpdateNote(userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ noteId, updateData }: { noteId: string; updateData: NoteUpdateType }) =>
      authorizedFetch(`${BASE_URL}/api/notes/${noteId}`, {
        method: "PATCH",
        body: JSON.stringify(updateData),
      }),
    onSuccess: (_, { noteId }) => {
      qc.invalidateQueries({ queryKey: ["notes", userId] });
      qc.invalidateQueries({ queryKey: ["notes", noteId, userId] });
    },
  });
}

export function useSilentUpdateNote() {
  return useMutation({
    mutationFn: ({ noteId, updateData }: { noteId: string; updateData: NoteUpdateType }) =>
      authorizedFetch(`${BASE_URL}/api/notes/${noteId}?skip_indexing=true`, {
        method: "PATCH",
        body: JSON.stringify(updateData),
      }),
  });
}


export function useDeleteNote(userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (noteId: string) =>
      authorizedFetch(`${BASE_URL}/api/notes/${noteId}`, { method: "DELETE" }),
    onSuccess: (_, noteId) => {
      qc.invalidateQueries({ queryKey: ["notes", userId] });
      qc.invalidateQueries({ queryKey: ["notes", noteId, userId] });
    },
  });
}

// Folder API functions
export function useFolders(userId: string | null) {
  return useQuery({
    queryKey: ["folders", userId],
    queryFn: () => authorizedFetch(`${BASE_URL}/api/folders/`),
    staleTime: 0,
    refetchOnWindowFocus: false,
    select: (data) => data as FolderType[],
  });
}

export function useFolderById(folderId: string | null, userId: string | null) {
  return useQuery({
    queryKey: ["folders", folderId, userId],
    queryFn: () => authorizedFetch(`${BASE_URL}/api/folders/${folderId}`),
    enabled: !!folderId,
    staleTime: 0,
    select: (data) => data as FolderType,
  });
}

export function useCreateFolder(userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (newFolder: FolderCreateType) =>
      authorizedFetch(`${BASE_URL}/api/folders/`, {
        method: "POST",
        body: JSON.stringify(newFolder),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders", userId] });
    },
  });
}

export function useUpdateFolder(userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ folderId, updateData }: { folderId: string; updateData: FolderUpdateType }) =>
      authorizedFetch(`${BASE_URL}/api/folders/${folderId}`, {
        method: "PATCH",
        body: JSON.stringify(updateData),
      }),
    onSuccess: (_, { folderId }) => {
      qc.invalidateQueries({ queryKey: ["folders", userId] });
      qc.invalidateQueries({ queryKey: ["folders", folderId, userId] });
    },
  });
}

export function useDeleteFolder(userId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (folderId: string) =>
      authorizedFetch(`${BASE_URL}/api/folders/${folderId}`, { method: "DELETE" }),
    onSuccess: (_, folderId) => {
      qc.invalidateQueries({ queryKey: ["folders", userId] });
      qc.invalidateQueries({ queryKey: ["folders", folderId, userId] });
      // Also invalidate notes since folder deletion affects notes
      qc.invalidateQueries({ queryKey: ["notes", userId] });
    },
  });
}

// ── Chat API hooks ──────────────────────────────────────────────

export function useGlobalChat() {
  return useMutation({
    mutationFn: (payload: ChatRequestType) =>
      authorizedFetch(`${BASE_URL}/api/chat/`, {
        method: "POST",
        body: JSON.stringify(payload),
      }) as Promise<ChatResponseType>,
  });
}

export function useNoteChat(noteId: string) {
  return useMutation({
    mutationFn: (payload: ChatRequestType) =>
      authorizedFetch(`${BASE_URL}/api/chat/note/${noteId}`, {
        method: "POST",
        body: JSON.stringify(payload),
      }) as Promise<ChatResponseType>,
  });
}

// Standalone function (non-hook) for components that need direct calls
export async function sendGlobalChat(payload: ChatRequestType): Promise<ChatResponseType> {
  return authorizedFetch(`${BASE_URL}/api/chat/`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<ChatResponseType>;
}

export async function sendNoteChat(noteId: string, payload: ChatRequestType): Promise<ChatResponseType> {
  return authorizedFetch(`${BASE_URL}/api/chat/note/${noteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<ChatResponseType>;
}