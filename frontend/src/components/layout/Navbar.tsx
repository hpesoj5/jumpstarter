"use client";

import { useState } from "react";
import { User } from "lucide-react";
import AuthModal from "@/components/AuthModal";

export default function Navbar() {
  const [userMenu, setUserMenu] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "signup" | null>(null);

  return ( 
    <>
    <header className="flex justify-between items-center px-6 py-3 bg-white shadow-sm border-b border-gray-100">
      {/* Left - Placeholder */}
      <div className="w-16" />
      
      {/* Center - App name */}
      <h1 className="text-xl font-semibold text-gray-800">GoalTracker</h1>
      
      {/* Right - User */}
      <div className="relative w-16">
        <button
          onClick={() => setUserMenu((prev) => !prev)}
          className="flex items-center gap-2 text-gray-700 hover:text-black"
        >
          <User size={20} />
          <span>User</span>
        </button>
        {userMenu && (
          <div className="absolute right-0 mt-2 bg-white border rounded-lg shadow-md w-40">
            <button
                onClick={() => setAuthMode("login")}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100"
              >
                Sign In
              </button>
              <button
                onClick={() => setAuthMode("signup")}
                className="block w-full text-left px-4 py-2 hover:bg-gray-100"
              >
                Sign Up
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  alert("Logged out");
                }}
                className="block w-full text-left px-4 py-2 text-red-500 hover:bg-gray-100"
              >
                Logout
              </button>
          </div>
        )}
      </div>
    </header>
    {authMode && (
      <AuthModal
        mode={authMode}
        onClose={() => setAuthMode(null)}
      />
    )}
    </>
  );
}
