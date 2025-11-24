import { useState } from "react";
import api from "@/lib/api";

export const useAuth = () => {
    const [loading, setLoading] = useState(false);

    const login = async (email: string, password: string) => {
        setLoading(true);
        const res = await api.post("/auth/login", { email, password });
        localStorage.setItem("token", res.data.access_token);
        setLoading(false);
    };

    const signup = async (
        username: string,
        email: string,
        password: string
    ) => {
        setLoading(true);
        await api.post("/auth/signup", { username, email, password });
        setLoading(false);
    };

    const logout = () => localStorage.removeItem("token");

    return { login, signup, logout, loading };
};
