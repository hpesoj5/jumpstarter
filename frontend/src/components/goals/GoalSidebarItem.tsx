import { Calendar } from "lucide-react";

export default function GoalSidebarItem({ goal }: { goal: { id: number; title: string } }) {
    return (
    <button className="flex items-center gap-2 p-4 hover:bg-gray-100 text-gray-700 w-full text-left">
        <Calendar size={16} />
        <span>{goal.title}</span>
    </button>
    );
}
