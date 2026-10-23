import { createRoot } from "react-dom/client";
import { MotionConfig } from "framer-motion";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <MotionConfig reducedMotion="user">
      <App />
    </MotionConfig>
  </QueryClientProvider>,
);
