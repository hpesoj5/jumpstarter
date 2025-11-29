"use client";

import { PlusCircle, Target } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/api/config";
import GoalSidebarItem from "@/components/goals/GoalSidebarItem";

type Goal = { id: number; title: string };

export default function Sidebar() {
    const [goals, setGoals] = useState<Goal[]>([]);
    const router = useRouter();

    useEffect(() => {
        async function fetchGoals() {
            try {
                const res = await fetch(`${API_URL}/goals/titles`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${localStorage.getItem("token")}`,
                                "Content-Type": "application/json" }
                });
                const data: Goal[] = await res.json();
                setGoals(data);
            } catch (error) {
                console.error("Failed to fetch goals", error);
            }
        }
    
        fetchGoals();
    }, []);

    return (
        <aside className="w-64 h-full bg-white border-r border-gray-100 flex flex-col justify-between">
            {/* Top Section */}
            <div>
                <div className="p-4 border-b border-gray-100">
                    <h2 className="text-sm font-semibold text-gray-500">
                        My Goals
                    </h2>
                </div>
                <nav className="flex flex-col">
                    <button 
                        onClick={()=>{router.push("/dashboard")}}
                        className="flex items-center gap-2 p-4 hover:bg-gray-100 text-gray-700"
                    >
                        <Target size={18} />
                        <span>All Goals</span>
                    </button>

                    {goals.length > 0 &&
                        goals.map((goal) => (
                            <GoalSidebarItem key={goal.id} goal={goal} />
                        ))}
                </nav>
            </div>

            {/* Bottom - Create Goal */}
            <div className="p-4 border-t border-gray-100">
                <button 
                    className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
                    onClick={() => {router.push("/create")}}
                >
                    <PlusCircle size={18} />
                    <span>Create New Goal</span>
                </button>
            </div>
        </aside>
    );
}