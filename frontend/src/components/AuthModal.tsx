"use client";
import { useState } from "react";
import { login, signup } from "@/api/auth";

export default function AuthModal({ mode, onClose }: { mode: "login" | "signup", onClose: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const data = mode === "login"
        ? await login(email, password)
        : await signup(email, password);

      localStorage.setItem("token", data.access_token || "");
      alert(`${mode === "login" ? "Logged in" : "Signed up"} successfully!`);
      onClose();
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center">
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md space-y-4 w-80">
        <h2 className="text-xl font-semibold">{mode === "login" ? "Sign In" : "Sign Up"}</h2>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="border rounded px-3 py-2 w-full"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="border rounded px-3 py-2 w-full"
          required
        />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <div className="flex justify-end space-x-2">
          <button type="button" onClick={onClose} className="px-3 py-2 bg-gray-100 rounded">
            Cancel
          </button>
          <button type="submit" className="px-3 py-2 bg-indigo-600 text-white rounded">
            {mode === "login" ? "Sign In" : "Sign Up"}
          </button>
        </div>
      </form>
    </div>
  );
}
