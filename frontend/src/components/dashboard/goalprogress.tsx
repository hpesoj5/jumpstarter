"use client"
import { ReactNode } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import { CaretLeftIcon } from "@phosphor-icons/react/dist/ssr/CaretLeft";
import { CaretRightIcon } from "@phosphor-icons/react/dist/ssr/CaretRight";
import IconButton from "@mui/material/IconButton";
import { PieChart } from "@mui/x-charts/PieChart";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

export interface Goal {
    title: string,
    total_dailies: number,
    completed_dailies: number,
    deadline: Date,
};    

interface ProgressCardProps {
    goal: Goal,
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

export function ProgressCard({ goal, current_date }: ProgressCardProps) {
    const millisecondsInADay = 1000 * 60 * 60 * 24;
    const daysRemaining = Math.ceil((goal.deadline.getTime() - current_date.getTime()) / millisecondsInADay);
    const dailiesRemaining = goal.total_dailies - goal.completed_dailies;

    const chartWidth = 200
    const chartHeight = 200

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
                <IconButton aria-label="previous">
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
                                    innerRadius: "80%",
                                    startAngle: 0,
                                    endAngle: 360 * goal.completed_dailies / goal.total_dailies,
                                }                    
                            ]}
                            height={chartHeight}
                            width={chartWidth}
                            slotProps={{ tooltip: { trigger: "none" } }}
                        >
                        </PieChart>
                        <DonutCenterLabel>
                            <Typography variant="h5">{goal.completed_dailies/goal.total_dailies*100}%</Typography>
                            </DonutCenterLabel>
                    </Box>
                    <Box
                        sx={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                        }}
                    >
                        <Typography variant="h6">{goal.title}</Typography>
                        <Typography color="text.secondary" variant="body1">{daysRemaining} days remaining</Typography>
                        <Typography color="text.secondary" variant="body1">{dailiesRemaining} remaining tasks</Typography>
                    </Box>
                </Stack>
                <IconButton aria-label="next" sx={{  }}>
                    <CaretRightIcon />
                </IconButton>
            </Stack>
        </Card>
    );
}
