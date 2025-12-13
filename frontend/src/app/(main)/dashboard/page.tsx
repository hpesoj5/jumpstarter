"use client"
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Grid from "@mui/material/Grid";
import { getStats, getGoalProgress } from "@/api/dashboard";
import { isExpired } from "@/api/auth";
import { StatCard } from "@/components/dashboard/StatCard";
import { Daily, DailyTable, EmptyDailies } from "@/components/dashboard/DailyList";
import { ProgressCard } from "@/components/dashboard/GoalProgressCard";

interface Stats {
    remaining_tasks_today: number,
    completed_tasks_today: number,
    ongoing_goals: number,
    completed_goals: number,
    tasks_today_list: Daily[],
}

export interface Goal {
    title: string,
    total_dailies: number,
    completed_dailies: number,
    deadline: string,
};    

export default function Dashboard() {
    const router = useRouter();
    const [stats, setStats] = useState<Stats>({
        remaining_tasks_today: 0,
        completed_tasks_today: 0,
        ongoing_goals: 0,
        completed_goals: 0,
        tasks_today_list: [],
    });
    const [goals, setGoals] = useState<Goal[]>([]);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (isExpired(token)) {
            localStorage.removeItem("token");
            router.push("/");
        }
    });

    useEffect(() => {
        const loadStats = async () => {
            const data = await getStats();
            setStats(data);
            const goalData = await getGoalProgress();
            setGoals(goalData.goals);
        };
        loadStats();
    }, []);

    console.log(stats);

    return (
        <Grid container spacing={3}>
            <Grid size={{ lg: 3, sm: 6, xs: 12 }}>
                <StatCard stat="Remaining Tasks Today" value={stats?.remaining_tasks_today} sx={{ height: '100%' }} />
            </Grid>
            <Grid size={{ lg: 3, sm: 6, xs: 12 }}>
                <StatCard stat="Completed Tasks Today" value={stats?.completed_tasks_today} sx={{ height: '100%' }} />
            </Grid>
            <Grid size={{ lg: 3, sm: 6, xs: 12 }}>
                <StatCard stat="Ongoing Goals" value={stats?.ongoing_goals} sx={{ height: '100%' }} />
            </Grid>
            <Grid size={{ lg: 3, sm: 6, xs: 12 }}>
                <StatCard stat="Completed Goals" value={stats?.completed_goals} sx={{ height: '100%' }} />
            </Grid>
            <Grid size={{ lg: 8, sm: 12 }}>
                {stats?.remaining_tasks_today > 0 ? (
                    <DailyTable
                        count={stats?.tasks_today_list.length}
                        page={0}
                        rows={stats?.tasks_today_list}
                        rowsPerPage={stats?.tasks_today_list.length}
                    />
                ) : (
                    <EmptyDailies/>
                )}
            </Grid>
            <Grid size={{ lg: 4, sm: 12 }}>
                <ProgressCard
                    goals={goals}
                    current_date={new Date()}
                />
            </Grid>
        </Grid>
    );
}
