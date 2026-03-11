import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Brain, Plus, Search, MessageSquare, FileText, Folder, LogOut, Sparkles, MoreVertical, Star, Trash2, FolderInput } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/lib/authContext";

import { 
  NoteType, 
  useDeleteNote, 
  useNotes, 
  useUpdateNote,
  FolderType,
  useFolders,
  useCreateFolder,
  useDeleteFolder
} from "@/lib/apiClient";
import { useQueryClient } from "@tanstack/react-query";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";



const Dashboard = () => {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const { signOut, user } = useAuth();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFolder, setSelectedFolder] = useState("All Notes");
  const [newFolderName, setNewFolderName] = useState("");
  const [isAddingFolder, setIsAddingFolder] = useState(false);
  const [folderToDelete, setFolderToDelete] = useState<{ id: string; name: string } | null>(null);

  // Folder queries and mutations
  const { data: folders = [], isLoading: isLoadingFolders } = useFolders(user?.id || null);
  const createFolderMutation = useCreateFolder(user?.id || null);
  const deleteFolderMutation = useDeleteFolder(user?.id || null);

  // Variables for note state
  const { data: notes = [], isLoading: isLoadingNotes, error } = useNotes(user?.id || null);
  const updateNoteMutation = useUpdateNote(user?.id || null);
  const deleteNoteMutation = useDeleteNote(user?.id || null);

  const handleLogout = async () => {
    try {
      await signOut();
      toast.success("Logged out successfully");
      navigate("/");
    } catch (error) {
      toast.error("Error logging out");
    }
  };

  const handleAddFolder = async () => {
    if (newFolderName.trim() && !folders.some(f => f.name === newFolderName.trim())) {
      try {
        await createFolderMutation.mutateAsync({ name: newFolderName.trim() });
        setNewFolderName("");
        setIsAddingFolder(false);
        toast.success(`Folder "${newFolderName.trim()}" created`);
      } catch (error: any) {
        toast.error(`Failed to create folder: ${error.message}`);
      }
    }
  };

  const handleDeleteFolder = async () => {
    if (!folderToDelete) return;
    
    try {
      await deleteFolderMutation.mutateAsync(folderToDelete.id);
      
      // If the deleted folder was selected, switch to "All Notes"
      if (selectedFolder === folderToDelete.name) {
        setSelectedFolder("All Notes");
      }
      
      toast.success(`Folder "${folderToDelete.name}" deleted`);
    } catch (error: any) {
      toast.error(`Failed to delete folder: ${error.message}`);
    } finally {
      setFolderToDelete(null);
    }
  };

  // ---- Functions related to Notes

  const handleNewNote = () => {
    navigate("/editor");
  };

  const handleDeleteNote = async (noteId: string) => {
    try {
      await deleteNoteMutation.mutateAsync(noteId);
      toast.success("Note moved to trash");
    } catch (error: any) {
      
    }
  };

  const handleToggleStar = async (noteId: string, currentStarred: boolean) => {
    try {
      await updateNoteMutation.mutateAsync({
        noteId,
        updateData: { is_starred: !currentStarred },
      });
      toast.success(
        !currentStarred ? "Added to starred" : "Removed from starred"
      );
    } catch (error: any) {
      toast.error(`Failed to star note: ${error.message}`);
    }
  };

  const handleMoveNote = async (noteId: string, newFolderId: string, newFolderName: string) => {
    try {
      await updateNoteMutation.mutateAsync({
        noteId,
        updateData: { folder_id: newFolderId }, // use folder_id, not folder
      });
      toast.success(`Note moved to ${newFolderName}`);
    } catch (error: any) {
      toast.error(`Failed to move note: ${error.message}`);
    }
  };

  const filteredNotes = useMemo(
    () =>
      notes
        .filter((note) => !note.is_trashed)
        .filter((note) => {
          if (selectedFolder === "All Notes") return true;
          return note.folder === selectedFolder;
        })
        .filter((note) => {
          return (
            note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (note.content &&
              note.content.toLowerCase().includes(searchQuery.toLowerCase()))
          );
        }),
    [notes, selectedFolder, searchQuery]
  );

  const starredNotes = useMemo(
    () => notes.filter((note) => note.is_starred && !note.is_trashed),
    [notes]
  );
  // ------

  if (isLoadingNotes) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-subtle gap-4">
        <div className="relative">
          <Brain className="h-12 w-12 text-primary animate-pulse" />
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
          <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
          <div className="h-2 w-2 rounded-full bg-primary animate-bounce" />
        </div>
        <p className="text-muted-foreground text-sm">Loading your notes...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              NotaRAG
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-1 space-y-4">
            <Button
              variant="gradient"
              className="w-full"
              onClick={handleNewNote}
            >
              <Plus className="h-4 w-4" />
              New Note{" "}
              {selectedFolder !== "All Notes" && `in ${selectedFolder}`}
            </Button>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg">Folders</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsAddingFolder(!isAddingFolder)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-2">
                {isAddingFolder && (
                  <div className="flex gap-2 mb-2">
                    <Input
                      placeholder="Folder name"
                      value={newFolderName}
                      onChange={(e) => setNewFolderName(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleAddFolder()}
                      className="h-8 text-sm"
                      autoFocus
                    />
                    <Button
                      size="sm"
                      onClick={handleAddFolder}
                      className="h-8 px-2"
                    >
                      Add
                    </Button>
                  </div>
                )}
                <button
                  onClick={() => setSelectedFolder("All Notes")}
                  className={`w-full flex items-center gap-2 p-2 rounded-lg transition-colors text-left ${
                    selectedFolder === "All Notes"
                      ? "bg-primary/10 text-primary font-medium"
                      : "hover:bg-accent"
                  }`}
                >
                  <Folder className="h-4 w-4" />
                  <span className="text-sm">All Notes</span>
                </button>
                {folders.map((folder) => (
                  <div
                    key={folder.id}
                    className={`w-full flex items-center gap-2 p-2 rounded-lg transition-colors group ${
                      selectedFolder === folder.name
                        ? "bg-primary/10 text-primary font-medium"
                        : "hover:bg-accent"
                    }`}
                  >
                    <button
                      onClick={() => setSelectedFolder(folder.name)}
                      className="flex items-center gap-2 flex-1 text-left"
                    >
                      <Folder className="h-4 w-4" />
                      <span className="text-sm">{folder.name}</span>
                    </button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => setFolderToDelete({ id: folder.id, name: folder.name })}
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete Folder
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate("/search")}
                >
                  <Search className="h-4 w-4" />
                  Semantic Search
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate("/chat")}
                >
                  <MessageSquare className="h-4 w-4" />
                  Chat with Notes
                </Button>
              </CardContent>
            </Card>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3">
            <Tabs defaultValue="notes" className="w-full">
              <div className="flex items-center justify-between mb-6">
                <TabsList>
                  <TabsTrigger value="notes">My Notes</TabsTrigger>
                  <TabsTrigger value="recent">Recent</TabsTrigger>
                  <TabsTrigger value="starred">Starred</TabsTrigger>
                </TabsList>

                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search notes..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              <TabsContent value="notes" className="space-y-4">
                {filteredNotes.length === 0 ? (
                  <p className="text-center text-muted-foreground py-12">
                    No notes in this folder
                  </p>
                ) : (
                  filteredNotes.map((note) => (
                    <Card
                      key={note.id}
                      className="hover:shadow-elegant transition-all duration-300"
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div
                            className="flex-1 cursor-pointer"
                            onClick={() => navigate(`/editor/${note.id}`, { state: { note } })}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <CardTitle className="text-xl">
                                {note.title}
                              </CardTitle>
                              {note.is_starred && (
                                <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                              )}
                            </div>
                            <CardDescription>
                              {note.content.substring(0, 100)}...
                            </CardDescription>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleStar(note.id, note.is_starred);
                                }}
                              >
                                <Star
                                  className={`h-4 w-4 mr-2 ${
                                    note.is_starred
                                      ? "fill-yellow-500 text-yellow-500"
                                      : ""
                                  }`}
                                />
                                {note.is_starred ? "Unstar" : "Star"}
                              </DropdownMenuItem>
                              <DropdownMenuSub>
                                <DropdownMenuSubTrigger>
                                  <FolderInput className="h-4 w-4 mr-2" />
                                  Move to folder
                                </DropdownMenuSubTrigger>
                                <DropdownMenuSubContent>
                                  {folders
                                    .filter(
                                      (f) =>
                                        f.name !== note.folder
                                    )
                                    .map((folder) => (
                                      <DropdownMenuItem
                                        key={folder.id}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleMoveNote(note.id, folder.id, folder.name);
                                        }}
                                      >
                                        <Folder className="h-4 w-4 mr-2" />
                                        {folder.name}
                                      </DropdownMenuItem>
                                    ))}
                                </DropdownMenuSubContent>
                              </DropdownMenuSub>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteNote(note.id);
                                }}
                                className="text-destructive"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex gap-2">
                            {[].map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">
                              {note.folder}
                            </span>{" "}
                            {/*I suppose this needs to be folder_id after making changes*/}
                            <span className="text-xs text-muted-foreground">
                              •
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(note.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}

                {/* AI Suggestion Card */}
                <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-accent/5">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className="h-10 w-10 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0">
                        <Sparkles className="h-5 w-5 text-primary-foreground" />
                      </div>
                      <div>
                        <h3 className="font-semibold mb-2">AI Insight</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Your notes about Machine Learning and React have
                          common patterns. Would you like to create a connection
                          between these topics?
                        </p>
                        <Button variant="outline" size="sm">
                          Explore Connections
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="recent">
                <p className="text-center text-muted-foreground py-12">
                  Recent notes will appear here
                </p>
              </TabsContent>

              <TabsContent value="starred" className="space-y-4">
                {starredNotes.length === 0 ? (
                  <p className="text-center text-muted-foreground py-12">
                    No starred notes yet
                  </p>
                ) : (
                  starredNotes.map((note) => (
                    <Card
                      key={note.id}
                      className="hover:shadow-elegant transition-all duration-300"
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div
                            className="flex-1 cursor-pointer"
                            onClick={() => navigate(`/editor/${note.id}`, { state: { note } })}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <CardTitle className="text-xl">
                                {note.title}
                              </CardTitle>
                              <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                            </div>
                            <CardDescription>
                              {note.content.substring(0, 100)}
                            </CardDescription>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleStar(note.id, note.is_starred);
                                }}
                              >
                                <Star className="h-4 w-4 mr-2 fill-yellow-500 text-yellow-500" />
                                Unstar
                              </DropdownMenuItem>
                              <DropdownMenuSub>
                                <DropdownMenuSubTrigger>
                                  <FolderInput className="h-4 w-4 mr-2" />
                                  Move to folder
                                </DropdownMenuSubTrigger>
                                <DropdownMenuSubContent>
                                  {folders
                                    .filter(
                                      (f) =>
                                        f.name !== note.folder
                                    )
                                    .map((folder) => (
                                      <DropdownMenuItem
                                        key={folder.id}
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleMoveNote(note.id, folder.id, folder.name);
                                        }}
                                      >
                                        <Folder className="h-4 w-4 mr-2" />
                                        {folder.name}
                                      </DropdownMenuItem>
                                    ))}
                                </DropdownMenuSubContent>
                              </DropdownMenuSub>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteNote(note.id);
                                }}
                                className="text-destructive"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex gap-2">
                            {note.tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">
                              {note.folder}
                            </span>{" "}
                            {/*I suppose this needs to be folder_id after making changes*/}
                            <span className="text-xs text-muted-foreground">
                              •
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(note.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </TabsContent>
            </Tabs>
          </main>
        </div>
      </div>

      {/* Delete Folder Confirmation Dialog */}
      <AlertDialog open={!!folderToDelete} onOpenChange={() => setFolderToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Folder</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the folder "{folderToDelete?.name}"? This action cannot be undone.
              {selectedFolder === folderToDelete?.name && " You will be redirected to All Notes."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteFolder}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Dashboard;