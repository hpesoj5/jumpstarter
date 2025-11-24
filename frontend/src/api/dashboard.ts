
import { API_URL } from "@/api/config";

export async function getStats() {
    const res = await fetch(`${API_URL}/dashboard/stats`, {
        method: "GET",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        }
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to fetch stats");
    }
    return res.json();
}
