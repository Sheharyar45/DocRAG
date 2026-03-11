import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Brain, ArrowLeft, Save, Sparkles, Tag, MessageSquare } from "lucide-react";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import { toast } from "sonner";
import NoteChat from "@/components/NoteChat";
import { useAuth } from "@/lib/authContext";
import { NoteType, useUpdateNote, useCreateNote, NoteUpdateType, useNoteById, useSilentUpdateNote } from "@/lib/apiClient";

const Editor = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { noteId } = useParams<{ noteId: string }>();
  const { user } = useAuth();
  const { data: fetchedNote, isLoading: noteLoading } = useNoteById(noteId, user?.id || null);
  const [title, setTitle] = useState(location.state?.note ? location.state.note.title : "");
  const [content, setContent] = useState(location.state?.note ? location.state.note.content : "");
  const [isNewNote, setIsNewNote] = useState(true);
  const [loading, setLoading] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const createNoteMutation = useCreateNote(user?.id || null);
  const updateNoteMutation = useUpdateNote(user?.id || null);
  const silentUpdateNoteMutation = useSilentUpdateNote();

  useEffect(() => {
    if (noteLoading) return; // <-- WAIT until request finished

    if (noteId && location.state?.note) {
      setIsNewNote(false);
      setTitle(location.state.note.title);
      setContent(location.state.note.content);
      setTags(location.state.note.tags || []);
      return;
    }

    if (noteId && fetchedNote) {
      setIsNewNote(false);
      setTitle(fetchedNote.title);
      setContent(fetchedNote.content);
      setTags(fetchedNote.tags || []);
      return;
    }

    // NEW NOTE
    if (!noteId) {
      setIsNewNote(true);
      setTitle("");
      setContent("");
      setTags([]);
    }
  }, [noteId, location.state?.note, fetchedNote, noteLoading]);

  const debounce = (fn: Function, delay: number) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  };

  const debouncedSave = useMemo(
    () =>
      debounce((update) => {
        silentUpdateNoteMutation.mutate({
          noteId,
          updateData: update,
        });
      }, 4000),
    [noteId, silentUpdateNoteMutation]
  );

  useEffect(() => {
    if (!noteId || isNewNote) return;

    debouncedSave({
      title,
      content,
      tags,
    });
  }, [title, content, tags]);



  const handleSave = async () => {
    if (!user) {
      toast.error("You must be logged in to save a note.");
      return;
    }

    if (!title.trim() || !content.trim()) {
      toast.error("Title and content cannot be empty.");
      return;
    }

    setLoading(true);

    try {
      if (isNewNote) {
        // CREATE NEW NOTE
        const newNoteData = {
          title: title.trim(),
          content: content.trim(),
          user_id: user.id,
        };
        await createNoteMutation.mutateAsync(newNoteData);
        toast.success(`Note "${title.trim()}" created successfully!`);
      } else if (noteId) {
        // UPDATE EXISTING NOTE
        const updateData: NoteUpdateType = {
          title: title.trim(),
          content: content.trim(),
        };
        await updateNoteMutation.mutateAsync({
          noteId,
          updateData,
        });
        toast.success(`Note "${title.trim()}" updated successfully!`);
      }

      navigate("/dashboard");
    } catch (error: any) {
      toast.error(`Failed to save note: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  const handleAutoTag = () => {
    toast.success("AI is analyzing your note...");
    setTimeout(() => {
      const suggestedTags = ["Study", "Important", "Review"];
      setTags([...new Set([...tags, ...suggestedTags])]);
      toast.success("Tags suggested!");
    }, 1500);
  };


  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                NotaRAG
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleAutoTag} disabled={loading}>
              <Sparkles className="h-4 w-4" />
              Auto-Tag
            </Button>
            <Button
              variant="outline"
              onClick={() => setIsChatOpen(!isChatOpen)}
              className={isChatOpen ? "bg-primary/10" : ""}
              disabled={loading}
            >
              <MessageSquare className="h-4 w-4" />
              Chat with Note
            </Button>
            <Button variant="hero" onClick={handleSave} disabled={loading}>
              <Save className="h-4 w-4" />
              {isNewNote ? "Save Note" : "Update Note"}
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 flex gap-4">
        {loading ? (
          <div className="w-full text-center py-20 text-muted-foreground">
            Loading Note...
          </div>
        ) : (
          <Card
            className={`p-8 shadow-elegant transition-all duration-300 ${
              isChatOpen ? "flex-1" : "max-w-4xl mx-auto w-full"
            }`}
          >
            <div className="space-y-6">
              {/* Title */}
              <div>
                <Input
                  placeholder="Note Title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="text-3xl font-bold border-0 px-0 focus-visible:ring-0 placeholder:text-muted-foreground/50"
                />
              </div>

              {/* Tags */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">
                    Tags
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium flex items-center gap-2 cursor-pointer hover:bg-primary/20 transition-colors"
                      onClick={() => handleRemoveTag(tag)}
                    >
                      {tag}
                      <span className="text-xs">×</span>
                    </span>
                  ))}
                  <Input
                    placeholder="Add tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleAddTag()}
                    className="w-32 h-8 text-sm"
                  />
                </div>
              </div>

              {/* Content */}
              <div>
                <Textarea
                  placeholder="Start writing your note... (Markdown supported)"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="min-h-[500px] text-lg border-0 px-0 focus-visible:ring-0 resize-none"
                />
              </div>

              {/* Tips */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  Tips for Better Notes
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Use descriptive titles for better semantic search</li>
                  <li>• Add relevant tags to organize your notes</li>
                  <li>• Write in clear, complete sentences for AI chat</li>
                  <li>• Use Markdown for formatting (# headers, **bold**, etc.)</li>
                </ul>
              </div>
            </div>
          </Card>
        )}

        {/* Chat Panel */}
        {isChatOpen && !loading && (
          <div className="w-96 animate-slide-in-right">
            <NoteChat
              onClose={() => setIsChatOpen(false)}
              noteTitle={title || "Untitled Note"}
              noteId={noteId}
              noteContent={content}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Editor;