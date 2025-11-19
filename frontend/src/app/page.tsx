"use client"
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Carousel } from "@/components/layout/Carousel";
import AuthModal from "@/components/AuthModal";

export default function HomePage() {
  const [authMode, setAuthMode] = useState<"login" | "signup" | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      router.push("/dashboard"); // redirect signed-in users
    }
  }, []);
  
  return (
    <div className="flex flex-col md:flex-row h-full pt-32 pb-28 bg-gradient-to-b from-white to-indigo-400 overflow-hidden">
        <div className="max-w-6xl mx-auto text-left mb-8 px-6">
          <h2 className="text-5xl font-extrabold leading-tight">Build Your Tomorrow,</h2>
          <h2 className="text-5xl font-extrabold text-indigo-600 leading-tight">Today.</h2>
          <p className="mt-6 text-gray-600 mx-auto">
            Planning can be tedious.<br/>
            That shouldn’t stop you from achieving your dreams.<br/>
            [GoalTracker] helps you define SMART goals and creates a plan that works for you.<br/>
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
          "https://cdn.stickerrs.com/StickerPacks/tQsH9FxPP7CQJvy9cIb3/23040BD3-35F1-4C21-A4E9-E5077EC5C91E_100x100.png",
          "https://cdn.stickerrs.com/StickerPacks/tQsH9FxPP7CQJvy9cIb3/3CE54C4C-C0A7-4F47-8A3B-955ECC66E11A_100x100.png",
          "https://cdn.stickerrs.com/StickerPacks/tQsH9FxPP7CQJvy9cIb3/25C9852E-5B73-4273-AC62-B1F795F5F5E8_100x100.png",
          "https://cdn.stickerrs.com/StickerPacks/tQsH9FxPP7CQJvy9cIb3/B7A019AC-7D90-44BC-BAFC-5785AD778770_100x100.png",
          "https://cdn.stickerrs.com/StickerPacks/tQsH9FxPP7CQJvy9cIb3/ED79660D-46F3-4740-B6F1-616A638D56F8_100x100.png",
        ]}
        />
        {authMode && (
          <AuthModal
            mode={authMode}
            onClose={() => setAuthMode(null)}
          />
        )}
    </div>
  );
}
