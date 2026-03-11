import { ArrowRight, Brain, Search, MessageSquare, Sparkles, BookOpen, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import heroBackground from "@/assets/hero-background.jpg";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Navigation */}
      <nav className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              NotaRAG
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/auth")}>
              Sign In
            </Button>
            <Button variant="hero" onClick={() => navigate("/auth")}>
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 md:py-32">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url(${heroBackground})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-4xl mx-auto text-center animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
              <Sparkles className="h-4 w-4" />
              <span className="text-sm font-medium">AI-Powered Note Taking</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Your Notes,{" "}
              <span className="bg-gradient-hero bg-clip-text text-transparent">
                Intelligently Connected
              </span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              NotaRAG uses semantic search and AI to help you find, understand, and chat with your notes. 
              Never lose an important insight again.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                variant="gradient"
                size="lg"
                onClick={() => navigate("/auth")}
                className="text-lg"
              >
                Start Taking Smarter Notes
                <ArrowRight className="h-5 w-5" />
              </Button>
              <Button variant="outline" size="lg" className="text-lg">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-slide-up">
            <h2 className="text-4xl font-bold mb-4">Powerful Features for Modern Learning</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Built for students, researchers, and knowledge workers who want more from their notes
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-2 hover:shadow-elegant transition-all duration-300 animate-scale-in">
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-lg bg-gradient-primary flex items-center justify-center mb-4">
                  <Search className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-bold mb-2">Semantic Search</h3>
                <p className="text-muted-foreground">
                  Find notes by meaning, not just keywords. Our AI understands context and relationships between your ideas.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 hover:shadow-elegant transition-all duration-300 animate-scale-in" style={{ animationDelay: "0.1s" }}>
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-lg bg-gradient-primary flex items-center justify-center mb-4">
                  <MessageSquare className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-bold mb-2">Chat with Your Notes</h3>
                <p className="text-muted-foreground">
                  Ask questions and get instant answers from your entire knowledge base using RAG technology.
                </p>
              </CardContent>
            </Card>

            <Card className="border-2 hover:shadow-elegant transition-all duration-300 animate-scale-in" style={{ animationDelay: "0.2s" }}>
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-lg bg-gradient-primary flex items-center justify-center mb-4">
                  <BookOpen className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-bold mb-2">Smart Organization</h3>
                <p className="text-muted-foreground">
                  Auto-tagging and topic detection keep your notes organized without the manual work.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gradient-subtle">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">How NotaRAG Works</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Advanced AI technology made simple
            </p>
          </div>
          <div className="max-w-4xl mx-auto space-y-8">
            {[
              {
                step: "1",
                title: "Create & Capture",
                description: "Write your notes with our intuitive editor. Markdown support included.",
              },
              {
                step: "2",
                title: "AI Processing",
                description: "Your notes are automatically embedded into a vector database for semantic understanding.",
              },
              {
                step: "3",
                title: "Search & Chat",
                description: "Find information instantly or have conversations with your knowledge base.",
              },
            ].map((item, idx) => (
              <div
                key={idx}
                className="flex gap-6 items-start p-6 rounded-lg bg-card border-2 hover:shadow-elegant transition-all duration-300"
              >
                <div className="h-12 w-12 rounded-full bg-gradient-primary flex items-center justify-center text-primary-foreground font-bold text-xl flex-shrink-0">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center p-12 rounded-2xl bg-gradient-hero shadow-glow">
            <Lock className="h-12 w-12 text-primary-foreground mx-auto mb-6" />
            <h2 className="text-4xl font-bold text-primary-foreground mb-4">
              Ready to Transform Your Note-Taking?
            </h2>
            <p className="text-xl text-primary-foreground/90 mb-8 max-w-2xl mx-auto">
              Join students and researchers using AI to unlock the full potential of their knowledge.
            </p>
            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate("/auth")}
              className="text-lg"
            >
              Start Free Today
              <ArrowRight className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-background">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Brain className="h-6 w-6 text-primary" />
              <span className="font-bold text-lg">NotaRAG</span>
            </div>
            <p className="text-muted-foreground text-sm">
              Built by CREATE UofT • Part of the student innovation ecosystem
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
