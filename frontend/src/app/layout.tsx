import React from "react";
import "./globals.css";
import Header from "@/components/Header";
import ThemeProviderWrapper from "@/theme/ThemeProvider";

export const metadata = {
  title: "AI Receptionist Pro",
  description: "Premium AI-powered business phone management platform",
};

export const dynamic = 'force-dynamic';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ThemeProviderWrapper>
          <Header />
          <main>
            {children}
          </main>
        </ThemeProviderWrapper>
      </body>
    </html>
  );
}
