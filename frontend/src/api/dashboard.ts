
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

export async function getGoalProgress(goalId: number | null = null) {
    const res = await fetch(`${API_URL}/dashboard/goal_progress`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal_id: goalId })
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to fetch goal progress");
    }
    return res.json();
}

export async function getTitle(goalId: number) {
    const res = await fetch(`${API_URL}/dashboard/get_title`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal_id: goalId })
    });

    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to fetch goal title");
    }
    return res.json();
}

export async function getPhases(goalId: number) {
    const res = await fetch(`${API_URL}/dashboard/get_phases`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal_id: goalId })
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `Failed to get phases for goal ${goalId}`);
    }
    return res.json();
}

export async function getDailies(goalId: number, completed: boolean) {
    const res = await fetch(`${API_URL}/dashboard/get_dailies`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal_id: goalId, completed: completed })
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `Failed to get daily tasks for goal ${goalId}`);
    }
    return res.json();
}

export async function markComplete(selectedIds: Array<number>, completed: boolean) {
    const res = await fetch(`${API_URL}/dashboard/mark_complete`, {
        method: "PATCH",
        headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ ids: selectedIds, completed: completed })
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to update daily status");
    }
    return res.json();
}
