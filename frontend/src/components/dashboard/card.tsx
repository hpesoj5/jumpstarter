import { JSX } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import type { SxProps } from '@mui/material/styles';
import Typography from '@mui/material/Typography';

export interface CardValue {
    stat: "Remaining Tasks Today" | "Completed Tasks Today" | "Ongoing Goals" | "Completed Goals",
    value: number,
    sx?: SxProps,
}

export function StatCard({stat, value, sx}: CardValue): JSX.Element {

    return (
        <Card sx={sx}>
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
