import { ReactNode } from "react";
import "@/styles/globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Navbar from "@/components/layout/Navbar";

export const metadata = {
title: "Dashboard",
description: "Track your goals and progress visually",
};

export default function DashboardLayout({ children }: { children: ReactNode }) {
    return (
        <>
            {/* Sidebar (left) */}
            <Sidebar />

            {/* Main content area */}
            <div className="flex flex-col flex-1 h-full overflow-hidden">
            <Navbar />
            <main className="p-6 flex-1 overflow-y-auto">{children}</main>
            </div>
        </>
    );
}
