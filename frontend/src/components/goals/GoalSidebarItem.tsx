import { Calendar } from "lucide-react";
import { useRouter } from "next/navigation";

export default function GoalSidebarItem({ goal }: { goal: { id: number; title: string } }) {
    const router = useRouter();
    const handleClick = () => {
        const slug = goal.id
        router.push(`/goal/${slug}`);
    };

    return (
    <button className="flex items-center gap-2 p-4 hover:bg-gray-100 text-gray-700 w-full text-left" onClick={() => handleClick()}>
        <Calendar size={16} />
        <span>{goal.title}</span>
    </button>
    );
}
