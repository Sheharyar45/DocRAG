import { Navigate } from "react-router-dom";
import { useAuth } from "@/lib/authContext";

type Props = {
  children: JSX.Element;
};

const PublicRoute: React.FC<Props> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return null; // or a loading spinner
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default PublicRoute;