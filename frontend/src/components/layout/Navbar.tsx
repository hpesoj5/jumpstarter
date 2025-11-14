"use client";

import { useState } from "react";
import { User } from "lucide-react";
import { jwtDecode } from "jwt-decode";
import { useClickAway } from "@uidotdev/usehooks";
import AuthModal from "@/components/AuthModal";

type TokenPayload = {
  sub?: string,
  username?: string,
  exp?: number, //convert to JS date by calling new Date(exp * 1000)
  iat?: number
};

const getUsername = (): string => {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) return "";
    const decoded = jwtDecode<TokenPayload>(token);
    return decoded.username ?? "";
  } catch {
    return "";
  }
};

export default function Navbar() {
  const [userMenu, setUserMenu] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "signup" | null>(null);
  const [username, setUsername] = useState(getUsername);
  const ref = useClickAway(() => {
    setUserMenu(false);
  }) as React.RefObject<HTMLDivElement | null>;

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
          <span>{username}</span>
        </button>
        {userMenu && (
          <div
            className="absolute right-0 mt-2 bg-white border rounded-lg shadow-md w-40"
            tabIndex={-1}
            ref={ref}
            >
              {username === "" && (
                <div>
                  <button
                    onClick={() => {
                      setUserMenu(false);
                      setAuthMode("login");
                    }}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => {
                      setUserMenu(false);
                      setAuthMode("signup");
                    }}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-100"
                  >
                    Sign Up
                  </button>
                </div>
              )}
              {username !== "" && (
                <button
                  onClick={() => {
                    setUserMenu(false);
                    localStorage.removeItem("token");
                    setUsername(getUsername);
                    alert("Logged out");
                  }}
                  className="block w-full text-left px-4 py-2 text-red-500 hover:bg-gray-100"
                >
                Logout
              </button>
              )}
          </div>
        )}
      </div>
    </header>
    {authMode && (
      <AuthModal
        mode={authMode}
        onClose={() => {
          setAuthMode(null);
          setUsername(getUsername);
        }}
      />
    )}
    </>
  );
}
