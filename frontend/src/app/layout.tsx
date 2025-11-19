import { ReactNode } from "react";
import "@/styles/globals.css";
import Navbar from "@/components/layout/Navbar";

export const metadata = {
  title: "GoalTracker",
  description: "Track your goals and progress visually",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="flex flex-row h-screen bg-gray-50 text-gray-900">

        {/* Main content area */}
        <div className="flex flex-col flex-1 h-full">
          <Navbar />
          <main className="flex-1 h-full">{children}</main>
        </div>

      </body>
    </html>
  );
}
