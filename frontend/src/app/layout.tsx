import { ReactNode } from "react";
import "@/styles/globals.css";

export const metadata = {
    title: "GoalTracker",
    description: "Track your goals and progress visually",
};

export default function RootLayout(
    { children, }:
    { children: React.ReactNode; }) {
    return (
        <html lang="en">
            <body className="flex flex-row h-screen bg-gray-50 text-gray-900">
                {children}
            </body>
        </html>
    );
}
