"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Note } from "@/lib/types";
import { Plus, Trash2 } from "lucide-react";

interface Props { entityType: string; entityId: string }

export function NoteEditor({ entityType, entityId }: Props) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [body, setBody] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const { data } = await api.get(`/notes?entity_type=${entityType}&entity_id=${entityId}`);
    setNotes(data);
  };

  useEffect(() => { load(); }, [entityId]);

  const save = async () => {
    if (!body.trim()) return;
    setSaving(true);
    await api.post("/notes", { entity_type: entityType, entity_id: entityId, body });
    setBody("");
    await load();
    setSaving(false);
  };

  const remove = async (id: string) => {
    await api.delete(`/notes/${id}`);
    await load();
  };

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-gray-700">Notes</h3>
      <div className="space-y-2">
        {notes.map(n => (
          <div key={n.id} className="bg-yellow-50 border border-yellow-200 rounded p-3 relative group">
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{n.body}</p>
            <p className="text-xs text-gray-400 mt-1">{new Date(n.updated_at).toLocaleDateString()}</p>
            <button
              onClick={() => remove(n.id)}
              className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 className="w-3.5 h-3.5 text-red-400" />
            </button>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <textarea
          value={body}
          onChange={e => setBody(e.target.value)}
          placeholder="Add a note…"
          rows={2}
          className="flex-1 text-sm border border-gray-200 rounded p-2 outline-none focus:border-blue-400 resize-none"
        />
        <button
          onClick={save}
          disabled={saving || !body.trim()}
          className="px-3 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50 hover:bg-blue-700 flex items-center gap-1"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
