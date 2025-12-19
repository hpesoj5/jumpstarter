"use client"
import { useState, useEffect } from "react";
import { redirect, useRouter } from "next/navigation";
import { isExpired } from "@/api/auth";
import { Carousel } from "@/components/layout/Carousel";
import AuthModal from "@/components/AuthModal";
import Navbar from "@/components/layout/Navbar";

export default function HomePage() {
    const [authMode, setAuthMode] = useState<"login" | "signup" | null>(null);
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (token && !isExpired(token)) {
            redirect("/dashboard"); // redirect signed-in users
        }
        else if (token) {
            localStorage.removeItem("token");
            router.refresh();
            window.location.reload();
        }
    });
  
  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto">
            <div className="flex flex-col md:flex-row h-full pt-32 pb-28 bg-gradient-to-b from-white to-indigo-400 overflow-hidden">
                <div className="max-w-6xl mx-auto text-left mb-8 px-6">
                    <h2 className="text-5xl font-extrabold leading-tight">Build Your Tomorrow,</h2>
                    <h2 className="text-5xl font-extrabold text-indigo-600 leading-tight">Today.</h2>

                    <p className="mt-6 text-gray-600 mx-auto">
                        Planning can be tedious.<br/>
                        That shouldn’t stop you from achieving your dreams.<br/>
                        JumpStarter helps you define SMART goals and creates a plan that works for you.<br/>
                        Track your progress. Stay motivated. Take actionable steps toward your goals!<br/>
                    </p>

                    <div className="mt-8 flex justify-left gap-4">
                        <button className="px-6 py-3 bg-indigo-600 text-white rounded-md text-lg hover:bg-indigo-800"
                            onClick={() => setAuthMode("signup")}>
                            Sign Up for Free
                        </button>
                        <button className="px-6 py-3 bg-gray-200 text-gray-800 rounded-md text-lg hover:bg-gray-300"
                            onClick={() => setAuthMode("login")}>
                            Log In
                        </button>
                    </div>
                </div>
                <Carousel
                    images={[
                    "/images/goal_view.png",
                    "/images/goal_definition.png",
                    "/images/phase_definition.png",
                    ]}
                />

                {authMode && (
                    <AuthModal
                        mode={authMode}
                        onClose={() => setAuthMode(null)}
                    />
                )}

            </div>
        </main>
    </div>
  );
}
