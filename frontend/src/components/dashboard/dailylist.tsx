"use client"
import { useMemo } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Checkbox from "@mui/material/Checkbox";
import dayjs from "dayjs";
import Divider from "@mui/material/Divider";
import { markComplete } from "@/api/dashboard";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableFooter from "@mui/material/TableFooter";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import { TablePaginationActionsProps } from "@mui/material/TablePaginationActions";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useSelection } from "@/hooks/useSelection";

export interface Daily {
    id: number,
    task_description: string,
    phase_title: string,
    start_time: string,
    estimated_time_minutes: number,
    is_completed: boolean,
};

export interface DailyTableProps {
    count: number,
    page: number,
    rows: Daily[],
    rowsPerPage: number,
    // we will be displaying all tasks in a single page in a vertically scrollable table
}

export function DailyTable({ count, page, rows, rowsPerPage }: DailyTableProps) {
    const rowIds = useMemo(() => {
        return rows.map((daily) => daily.id);
    }, [rows]);

    const { selectAll, deselectAll, selectOne, deselectOne, selected } = useSelection(rowIds);

    const selectedSome = (selected?.size ?? 0) > 0 && (selected?.size ?? 0) < rows.length;
    const selectedAll = rows.length > 0 && selected?.size === rows.length;
    const selectedAny = selectedSome || selectedAll;

    const SubmitButton = ({ disabled }: TablePaginationActionsProps) => {
        const handleClick = async () => {
            const selectedIds = Array.from(selected);
            await markComplete(selectedIds);
            window.location.reload()
        };

        return (
            <Button variant="contained" disabled={disabled} onClick={handleClick}>
                Mark as Completed
            </Button>
        );
    };

    return (
        <Card>
            <Box sx={{ overflow: "auto"}}>
                <Table sx={{ height: "72vh", minWidth: "800px"}}>
                    <TableHead>
                        <TableRow>
                            <TableCell padding="checkbox">
                                <Checkbox
                                    checked={selectedAll}
                                    indeterminate={selectedSome}
                                    onChange={(event) => {
                                        if (event.target.checked) {
                                            selectAll();
                                        } else {
                                            deselectAll();
                                        }
                                    }}
                                />
                            </TableCell>
                            <TableCell>Task</TableCell>                 {/* task description */}
                            <TableCell>Phase</TableCell>                {/* phase title */}
                            <TableCell>Start Time</TableCell>
                            <TableCell>Duration</TableCell>
                        </TableRow>             
                    </TableHead>
                    <TableBody>
                        {rows.map((row) => {
                            const isSelected = selected?.has(row.id);

                            return (
                                <TableRow hover key={row.id} selected={isSelected}>
                                    <TableCell padding="checkbox">
                                        <Checkbox
                                            checked={isSelected}
                                            onChange={(event) => {
                                                if (event.target.checked) {
                                                    selectOne(row.id);
                                                } else {
                                                    deselectOne(row.id);
                                                }
                                            }}
                                        />
                                    </TableCell>
                                    <TableCell>{row.task_description}</TableCell>
                                    <TableCell>{row.phase_title}</TableCell>
                                    <TableCell>{dayjs(new Date(`2000-01-01T${row.start_time}`)).format("h.mm A")}</TableCell>
                                    <TableCell>{row.estimated_time_minutes}</TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                    <TableFooter>
                        <TableRow>
                            <TablePagination
                                count={count}
                                page={page}
                                onPageChange={() => {}}
                                rowsPerPage={rowsPerPage}
                                rowsPerPageOptions={[]}
                                ActionsComponent={SubmitButton}
                                disabled={!selectedAny}
                            />
                        </TableRow>
                    </TableFooter>
                </Table>
            </Box>
        </Card>
    );
}

export function EmptyDailies() {
    return (
        <Card>
            <Box sx={{ height: "72vh", overflow: "auto", justifyContent: "center", flexDirection: "column", display: "flex" }}>
                <Typography textAlign="center" variant="h1">No Tasks Today</Typography>
                <Typography textAlign="center" variant="subtitle1">Check back tomorrow for more tasks!</Typography>
            </Box>
        </Card>
    );
}
