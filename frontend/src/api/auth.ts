import { jwtDecode } from "jwt-decode";
import { API_URL, type TokenPayload } from "@/api/config";

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

export const getUserId = (): number => {
    try {
        const token =
            typeof window !== "undefined"
                ? localStorage.getItem("token")
                : null;
        if (!token) return -1;
        const decoded = jwtDecode<TokenPayload>(token);
        return decoded.uid ?? -1;
    } catch {
        return -1;
    }
};
