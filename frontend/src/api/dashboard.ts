
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

export async function getGoalProgress() {
    const res = await fetch(`${API_URL}/dashboard/goal_progress`, {
        method: "GET",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        }
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to fetch goal progress");
    }
    return res.json();
}

export async function markComplete(selectedIds: Array<number>) {
    const res = await fetch(`${API_URL}/dashboard/mark_complete`, {
        method: "PATCH",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ ids: selectedIds })
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to update daily status");
    }
    return res.json();
}
