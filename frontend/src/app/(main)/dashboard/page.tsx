"use client"
import { useState, useEffect } from "react";
import { redirect } from "next/navigation";
import Grid from "@mui/material/Grid";
import { Goal, Stats } from "@/api/config";
import { getStats, getGoalProgress } from "@/api/dashboard";
import { isExpired } from "@/api/auth";
import StatCard from "@/components/dashboard/StatCard";
import { DailyTable, EmptyDailies } from "@/components/dashboard/DailyList";
import ProgressCard from "@/components/dashboard/GoalProgressCard";

export default function Dashboard() {
    // const router = useRouter();
    const [stats, setStats] = useState<Stats>({
        remaining_tasks_today: null,
        completed_tasks_today: null,
        ongoing_goals: null,
        completed_goals: null,
        tasks_today_list: [],
    });
    const [goals, setGoals] = useState<Goal[]>([]);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (isExpired(token)) {
            localStorage.removeItem("token");
            redirect("/");
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
                {(stats.remaining_tasks_today ?? 0) > 0 ? (
                    <DailyTable
                        count={stats.tasks_today_list.length}
                        page={0}
                        rows={stats.tasks_today_list}
                        rowsPerPage={stats.tasks_today_list.length}
                        completed={true}
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
