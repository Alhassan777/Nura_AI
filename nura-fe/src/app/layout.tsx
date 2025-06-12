import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import "./globals.css";
import Providers from "@/components/Providers";
import { ThemeProvider } from "@/components/theme-provider";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/contexts/AuthContext";
import MobileTopNav from "@/components/MobileTopNav";

const lexend = Lexend({
  variable: "--font-lexend",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});

const defaultUrl = process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(defaultUrl),
  title: "Nura: Your Personal Mental Health Companion",
  description: "Nura helps you understand and manage your mental well-being.",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning style={{ colorScheme: "light" }}>
      <body
        className={`${lexend.variable} ${lexend.className} antialiased h-full w-full`}
        style={{ fontFamily: "var(--font-lexend)" }}
      >
        <AuthProvider>
          <Providers>
            <ThemeProvider
              attribute="class"
              defaultTheme="light"
              disableTransitionOnChange
            >
              <main className="h-fit flex md:flex-row flex-col relative">
                <MobileTopNav />
                <Navbar />
                <div className="my-4 w-full px-3 sm:px-6 lg:px-8 flex-1 flex justify-center md:mb-0 mb-16 h-full md:min-h-screen min-h-fit">
                  {children}
                </div>
              </main>
            </ThemeProvider>
          </Providers>
        </AuthProvider>
      </body>
    </html>
  );
}
