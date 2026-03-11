import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, ArrowLeft, Search as SearchIcon, FileText, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { sendGlobalChat, SourceCitationType } from "@/lib/apiClient";
import { toast } from "sonner";

interface SearchResult {
  note_id: string;
  title: string;
  snippet: string;
  score: number;
}

const Search = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [aiSummary, setAiSummary] = useState("");

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(false);
    setResults([]);
    setAiSummary("");

    try {
      const response = await sendGlobalChat({
        query,
        search_mode: "hybrid",
        top_k: 8,
      });

      // Map sources to search results
      const searchResults: SearchResult[] = response.sources.map((s: SourceCitationType) => ({
        note_id: s.note_id,
        title: s.title,
        snippet: s.snippet,
        score: s.score,
      }));

      setResults(searchResults);
      setAiSummary(response.answer);
      setHasSearched(true);
    } catch (error: any) {
      toast.error(`Search failed: ${error.message}`);
    } finally {
      setIsSearching(false);
    }
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
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Search Header */}
        <div className="text-center mb-12">
          <div className="h-16 w-16 rounded-full bg-gradient-primary flex items-center justify-center mx-auto mb-4">
            <SearchIcon className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-4xl font-bold mb-4">Semantic Search</h1>
          <p className="text-xl text-muted-foreground">
            Find notes by meaning, not just keywords
          </p>
        </div>

        {/* Search Bar */}
        <Card className="shadow-elegant mb-8">
          <CardContent className="pt-6">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  placeholder="Ask a question or describe what you're looking for..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-10 h-12 text-lg"
                />
              </div>
              <Button variant="hero" size="lg" onClick={handleSearch} disabled={isSearching}>
                {isSearching ? "Searching..." : "Search"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Example Queries */}
        {!hasSearched && (
          <div className="mb-8">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Try asking:</h3>
            <div className="flex flex-wrap gap-2">
              {[
                "What are my notes about machine learning?",
                "Show me information on React optimization",
                "Find notes related to database design",
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => setQuery(example)}
                  className="px-4 py-2 rounded-lg bg-muted hover:bg-muted/80 text-sm transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {isSearching && (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-4" />
            <p className="text-muted-foreground">Analyzing semantic relationships...</p>
          </div>
        )}

        {hasSearched && !isSearching && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Search Results</h2>
              <span className="text-sm text-muted-foreground">{results.length} sources found</span>
            </div>

            {/* AI Summary */}
            {aiSummary && (
              <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-accent/5">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className="h-10 w-10 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0">
                      <Sparkles className="h-5 w-5 text-primary-foreground" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">AI Answer</h3>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">{aiSummary}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {results.length === 0 && (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No matching notes found. Try a different query.</p>
              </div>
            )}

            {results.map((result) => (
              <Card
                key={result.note_id}
                className="hover:shadow-elegant transition-all duration-300 cursor-pointer"
                onClick={() => navigate(`/editor/${result.note_id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <CardTitle className="text-xl">{result.title}</CardTitle>
                        <span className="px-2 py-1 rounded-full bg-accent/20 text-accent text-xs font-bold">
                          {(result.score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <CardDescription className="text-base">{result.snippet}</CardDescription>
                    </div>
                    <FileText className="h-5 w-5 text-muted-foreground" />
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
