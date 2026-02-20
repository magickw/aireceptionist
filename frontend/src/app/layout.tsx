import "./globals.css";
import Header from "@/components/Header";
import ThemeProviderWrapper from "@/theme/ThemeProvider";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";

// This file is now clean and only handles the root layout.
// API interceptors are handled in services/api.ts

export const metadata = {
  title: "Receptium",
  description: "Receptium - The Intelligent Frontline for your Business",
  icons: {
    icon: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ThemeProviderWrapper>
          <AuthProvider>
            <Header />
            <main>
              <ProtectedRoute>
                {children}
              </ProtectedRoute>
            </main>
          </AuthProvider>
        </ThemeProviderWrapper>
      </body>
    </html>
  );
}
