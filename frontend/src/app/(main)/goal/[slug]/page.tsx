"use client"
import BackButton from "@/components/goals/GoalDetailsBackButton";
import Box from "@mui/material/Box";
import { Daily } from "@/api/config";
import { DailyTable } from "@/components/goals/GoalDetailsDailyList";
import { getTitle, getDailies } from "@/api/dashboard";
import { isExpired } from "@/api/auth";
import Grid from "@mui/material/Grid";
import { redirect } from "next/navigation";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { use, useEffect, useState } from "react";

export default function GoalDetails({ params, }: {params: Promise<{ slug: string }>}) {
    const { slug } = use(params);
    const id = parseInt(slug);
    const [title, setTitle] = useState<string>("");
    const [uncompletedDailies, setUncompletedDailies] = useState<Daily[]>([]);
    const [completedDailies, setCompletedDailies] = useState<Daily[]>([]);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (isExpired(token)) {
            localStorage.removeItem("token");
            redirect("/");
        }
    });

    useEffect(() => {
        const loadStats = async () => {
            const res = await getTitle(id);
            if (res === null) {
                redirect("/dashboard");
            }
            setTitle(res);

            const data_uncompleted = await getDailies(id, false);
            const data_completed = await getDailies(id, true);
            setUncompletedDailies(data_uncompleted.dailies)
            setCompletedDailies(data_completed.dailies);
        };
        loadStats();
    }, [id]);

    return (
        <Stack
            direction="row"
            sx={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
            }}
            spacing={3}
        >
            <Box
                sx={{
                    height: "stretch",
                    alignItems: "top",
                    paddingTop: 1,
                }}
            >
                <BackButton />
            </Box>
            <Grid container rowSpacing={5} columnSpacing={3} width="stretch" paddingRight={8}>
                <Grid size={12}>
                    <Typography variant="h3">{title}</Typography>
                </Grid>
                <Grid size={{ lg: 6, sm: 12 }}>
                    <DailyTable
                        count={uncompletedDailies.length}
                        page={0}
                        rows={uncompletedDailies}
                        rowsPerPage={0}
                        completed={false}
                        
                    />
                </Grid>
                <Grid size={{ lg: 6, sm: 12 }}>
                    <DailyTable
                        count={completedDailies.length}
                        page={0}
                        rows={completedDailies}
                        rowsPerPage={0}
                        completed={true}
                    />
                </Grid>
            </Grid>
        </Stack>
    );
}
