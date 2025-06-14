"use client";

import { AntdRegistry } from "@ant-design/nextjs-registry";
import "@ant-design/v5-patch-for-react-19";
import { createRoot } from "react-dom/client";
import { ConfigProvider, theme, App, unstableSetRender } from "antd";
import { useEffect } from "react";
import axios from "axios";
import ReactQueryProvider from "./providers/react-query-provider";
import { InvitationNotificationProvider } from "@/contexts/InvitationNotificationContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  unstableSetRender((node, container: any) => {
    container._reactRoot ||= createRoot(container);
    const root = container._reactRoot;
    root.render(node);
    return async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
      root.unmount();
    };
  });

  useEffect(() => {
    axios.defaults.baseURL = process.env.NEXT_PUBLIC_BASE_URL;
  }, []);

  return (
    <ReactQueryProvider>
      <AntdRegistry>
        <ConfigProvider
          theme={{
            algorithm: theme.defaultAlgorithm,
            token: {
              fontFamily: "var(--font-lexend)",
              // your 4-color palette
              colorPrimary: "#9810fa", // teal for headers / primary buttons
              colorBgLayout: "#FFFFFF", // white page background
              colorBgContainer: "#FFFFFF", // white for cards / inputs
              colorTextBase: "#20232A", // dark text
            },
          }}
        >
          <App>
            <InvitationNotificationProvider>
              {children}
            </InvitationNotificationProvider>
          </App>
        </ConfigProvider>
      </AntdRegistry>
    </ReactQueryProvider>
  );
}
