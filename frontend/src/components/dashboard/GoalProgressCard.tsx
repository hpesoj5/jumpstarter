"use client"
import { ReactNode, useEffect, useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import { CaretLeftIcon } from "@phosphor-icons/react/dist/ssr/CaretLeft";
import { CaretRightIcon } from "@phosphor-icons/react/dist/ssr/CaretRight";
import { Goal } from "@/app/(main)/dashboard/page"
import IconButton from "@mui/material/IconButton";
import { PieChart } from "@mui/x-charts/PieChart";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface ProgressCardProps {
    goals: Goal[],
    current_date: Date,
};

function DonutCenterLabel({ children }: { children: ReactNode }) {
    
    return (
        <Box
            sx={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                textAlign: "center",
                pointerEvents: "none",        
            }}
        >
            {children}
        </Box>
    );
};

export function ProgressCard({ goals, current_date }: ProgressCardProps) {
    const millisecondsInADay = 1000 * 60 * 60 * 24;
    const [numGoals, setNumGoals] = useState<number>(0);
    const [page, setPage] = useState<number>(0);
    const [daysRemaining, setDaysRemaining] = useState<number>(0);
    const [dailiesRemaining, setDailiesRemaining] = useState<number>(0);
    const [proportion, setProportion] = useState<number>(0);
    const [title, setTitle] = useState<string>("");
    const chartWidth = 200;
    const chartHeight = 200;
    const innerRadius = 0.34 * chartWidth;
    const cornerRadius = innerRadius / 2;
    useEffect(() => {
        const loadGoalData = () => {
            // console.log(`Goals: ${JSON.stringify(goals)}`);
            if (!goals || goals.length === 0) return;

            const g = goals[0]
            const deadline = new Date(g.deadline);
            setNumGoals(goals.length);
            setPage(0);
            console.log(`Length of goal array: ${goals.length}`)
            setDaysRemaining(Math.floor((deadline.getTime() - current_date.getTime()) / millisecondsInADay));
            setDailiesRemaining(g.total_dailies - g.completed_dailies);
            setProportion(g.completed_dailies / g.total_dailies);
            setTitle(g.title);                
        };
        loadGoalData();
    }, [goals, current_date, millisecondsInADay]);

    const changePage = (increment: number) => {
        let newPage = page + increment;
        if (newPage < 0) {
            newPage += numGoals;
        }
        else if (newPage >= numGoals) {
            newPage -= numGoals;
        }
        console.log(`Old page: ${page}. New page: ${newPage}.`);
        setPage(newPage);
        const g = goals[newPage];
        const deadline = new Date(g.deadline);
        setDaysRemaining(Math.floor((deadline.getTime() - current_date.getTime()) / millisecondsInADay));
        setDailiesRemaining(g.total_dailies - g.completed_dailies);
        setProportion(g.completed_dailies / g.total_dailies);
        setTitle(g.title);
    }

    return (
        <Card>
            <Stack
                direction="row" 
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center", 
                    justifyContent: "space-between",
                    px: 2,
                    py: 4,
                }}
            >
                <IconButton aria-label="previous" onClick={() => {changePage(-1)}}>
                    <CaretLeftIcon />
                </IconButton>
                <Stack 
                    direction="column"
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        flexGrow: 1,
                        height: "100%",
                        alignItems: "center",
                    }}
                    spacing="5%"
                >
                    <Box
                        sx={{
                            position: "relative",
                            width: chartWidth,
                            height: chartHeight,
                        }}
                    >
                        <PieChart
                            series={[
                                {
                                    data: [
                                        { id: 0, value: 1},
                                    ],
                                    innerRadius: innerRadius,
                                    cornerRadius: cornerRadius,
                                    startAngle: 0,
                                    endAngle: 360 * proportion,
                                }                    
                            ]}
                            height={chartHeight}
                            width={chartWidth}
                            slotProps={{ tooltip: { trigger: "none" } }}
                        >
                        </PieChart>
                        <DonutCenterLabel>
                            <Typography variant="h5">{100 * proportion}%</Typography>
                            </DonutCenterLabel>
                    </Box>
                    <Box
                        sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                        }}
                    >
                        <Typography variant="h6">{title}</Typography>
                        <Typography color="text.secondary" variant="body1">{daysRemaining} days remaining</Typography>
                        <Typography color="text.secondary" variant="body1">{dailiesRemaining} remaining tasks</Typography>
                    </Box>
                </Stack>
                <IconButton aria-label="next" onClick={() => {changePage(1)}}>
                    <CaretRightIcon />
                </IconButton>
            </Stack>
        </Card>
    );
}
