"use client";

import { PlusCircle, Target } from "lucide-react";
import { useState } from "react";
import GoalSidebarItem from "@/components/goals/GoalSidebarItem";

export default function Sidebar() {
    const [goals] = useState<{ id: number; title: string }[]>([
        // { id: 1, title: "Learn React" },
        // { id: 2, title: "Run a Marathon" },
    ]);

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
                    <button className="flex items-center gap-2 p-4 hover:bg-gray-100 text-gray-700">
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
                <button className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium">
                    <PlusCircle size={18} />
                    <span>Create New Goal</span>
                </button>
            </div>
        </aside>
    );
}
