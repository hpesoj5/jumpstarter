"use client"
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Grid from "@mui/material/Grid";
import { getStats } from "@/api/dashboard";
import type { TokenPayload } from "@/api/config";
import { StatCard } from "@/components/dashboard/card";
import { jwtDecode } from "jwt-decode";

interface Stats {
    remaining_tasks_today: number,
    completed_tasks_today: number,
    ongoing_goals: number,
    completed_goals: number,
    tasks_today_list: [],
}

export default function Dashboard() {
    const router = useRouter();
    const [stats, setStats] = useState<Stats>({
        remaining_tasks_today: 0,
    completed_tasks_today: 0,
    ongoing_goals: 0,
    completed_goals: 0,
    tasks_today_list: [],
    });

    const isExpired = (token: string | null) => {
        if (!token) return true;
        try {
            const decodedToken = jwtDecode<TokenPayload>(token);
            const currentTime = Date.now() / 1000; // current time in seconds
            return decodedToken.exp! < currentTime;
        } catch (err) {
            console.error("Error decoding token:", err);
            return true;
        }
    };

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
        </Grid>
    );
}
