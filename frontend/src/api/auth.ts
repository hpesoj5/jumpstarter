import { jwtDecode } from "jwt-decode";
import { API_URL } from "@/api/config";
import type { TokenPayload } from "@/api/config";

export async function signup(username: string, email: string, password: string) {
    const res = await fetch(`${API_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Signup failed");
    }
    return res.json();
}

export async function login(email: string, password: string) {
    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Login failed");
    }
    return res.json(); // contains token
}

export const isExpired = (token: string | null) => {
    if (!token) return true;
    try {
        const decodedToken = jwtDecode<TokenPayload>(token);
        const currentTime = Date.now() / 1000; // current time in seconds
        return decodedToken.exp! < currentTime;
    } catch (err) {
        console.error("Error decoding token:", err);
        return true;
    }
};
