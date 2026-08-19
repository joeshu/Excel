import "antd/dist/reset.css";
import "./styles.css";
import { createRoot } from "react-dom/client";
import React from "react";
import { App } from "./AppShell";

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
