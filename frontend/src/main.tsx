import "antd/dist/reset.css";
import "./styles.css";
import { Component, type ErrorInfo, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import React from "react";
import { App } from "./AppShell";

type ErrorBoundaryState = { error?: Error };

class StartupErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = {};

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Excel Workflow UI 启动失败", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="startup-error">
          <h1>Excel 工作流暂时无法加载</h1>
          <p>界面脚本启动时发生错误。请重启应用；如果问题持续，请查看用户数据目录中的 <code>data/outputs/electron-backend.log</code>。</p>
          <details open>
            <summary>错误详情</summary>
            <pre>{this.state.error.stack ?? this.state.error.message}</pre>
          </details>
        </main>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <StartupErrorBoundary><App /></StartupErrorBoundary>
  </React.StrictMode>,
);
