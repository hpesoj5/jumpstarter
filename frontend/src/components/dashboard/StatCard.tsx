import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

export interface CardValue {
    stat: "Remaining Tasks Today" | "Completed Tasks Today" | "Ongoing Goals" | "Completed Goals",
    value: number | null,
}

export default function StatCard({stat, value}: CardValue) {

    return (
        <Card 
            sx={{
                height: "100%",
                borderRadius: 3,
                boxShadow: 5
            }}
        >
            <CardContent>
                <Stack spacing={3}>
                    <Stack direction="row" sx={{ alignItems: "flex-start", justifyContent: "space-between" }} spacing={3}>
                        <Stack spacing={1}>
                            <Typography color="text.secondary" variant="overline">
                                {stat}
                            </Typography>
                            <Typography variant="h4">{value}</Typography>
                        </Stack>
                    </Stack>
                </Stack>
            </CardContent>
        </Card>
    );
}
