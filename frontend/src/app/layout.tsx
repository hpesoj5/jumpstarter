import { ReactNode } from "react";
import "@/styles/globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Navbar from "@/components/layout/Navbar";

export const metadata = {
  title: "GoalTracker",
  description: "Track your goals and progress visually",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex flex-row h-screen bg-gray-50 text-gray-900">
        {/* Sidebar (left) */}
        {/*<Sidebar />*/}

        {/* Main content area */}
        <div className="flex flex-col flex-1 h-full overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>

      </body>
    </html>
  );
}
