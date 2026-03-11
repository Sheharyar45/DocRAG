import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/lib/authContext";

const ForgetPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false); 
  const { forgetPassword, loading: authLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast.warning("Please enter your email");
      return;
    }

    setIsLoading(true);
    try {
      await forgetPassword(email); 
      toast.success("Reset link sent to your email!");
      setIsSent(true); 
    } catch (err: any) {
      toast.error(err.message); 
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoBack = () => navigate("/auth");

  return (
    <div className="min-h-screen bg-gradient-subtle flex flex-col">
      <nav className="border-b bg-background/80 backdrop-blur-sm p-4">
        <button
          onClick={handleGoBack}
          className="flex items-center gap-2 text-muted-foreground"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back to Sign In</span>
        </button>
      </nav>

      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-elegant">
          <CardHeader>
            <CardTitle>Forget Password</CardTitle>
            <CardDescription>
              {isSent 
                ? "Check your email for the reset link (check spam folder too)!" 
                : "Enter your email to receive a password reset link"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!isSent ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading || authLoading}
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  variant="hero"
                  disabled={isLoading || authLoading}
                >
                  {isLoading || authLoading ? "Sending..." : "Send Reset Link"}
                </Button>
              </form>
            ) : (
              // Success state displayed after the link is sent
              <div className="space-y-4 text-center">
                <Button
                  type="button"
                  className="w-full"
                  variant="secondary"
                  onClick={handleGoBack}
                >
                  Go Back to Sign In
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ForgetPassword;