"use client"
import { useMemo } from "react";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Checkbox from "@mui/material/Checkbox";
import { DailyTableProps } from "@/api/config";
import dayjs from "dayjs";
import Divider from "@mui/material/Divider";
import { markComplete } from "@/api/dashboard";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableFooter from "@mui/material/TableFooter";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import { TablePaginationActionsProps } from "@mui/material/TablePaginationActions";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useSelection } from "@/hooks/useSelection";

const displayNothing = ({ from, to, count }) => {
    return (
        <>
        </>
    );
}

export function DailyTable({ count, page, rows, rowsPerPage, completed }: DailyTableProps) {
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
            await markComplete(selectedIds, !completed);
            window.location.reload()
        };

        return (
            <Button variant="contained" disabled={disabled} sx={{ margin: 1 }} onClick={handleClick}>
                Mark as {!completed ? "Complete" : "Uncomplete"}
            </Button>
        );
    };

    return (
        <Stack direction="column" spacing={1}>
            <Typography variant="h4">{completed ? "Completed Tasks" : "Uncompleted Tasks"}</Typography>
            <Card sx={{ borderRadius: 3, boxShadow: 5 }}>
                <TableContainer sx={{ height: "35vh", overflow: "auto" }}>
                    <Table stickyHeader>
                        <TableHead>
                            <TableRow>
                                <TableCell>Task</TableCell>
                                <TableCell>Phase</TableCell>
                                <TableCell>Date</TableCell>
                                <TableCell>Start Time</TableCell>
                                <TableCell>Duration</TableCell>
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
                            </TableRow>             
                        </TableHead>
                        <TableBody>
                            {rows.map((row) => {
                                const isSelected = selected?.has(row.id);

                                return (
                                    <TableRow hover key={row.id} selected={isSelected}>
                                        <TableCell>{row.task_description}</TableCell>
                                        <TableCell>{row.phase_title}</TableCell>
                                        <TableCell>{dayjs(new Date(row.dailies_date)).format("D MMM YY")}</TableCell>
                                        <TableCell>{dayjs(new Date(`2000-01-01T${row.start_time}`)).format("h.mm A")}</TableCell>
                                        <TableCell>{row.estimated_time_minutes}</TableCell>
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
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </TableContainer>
                <TablePagination
                    component="div"
                    count={count}
                    page={page}
                    onPageChange={() => {}}
                    rowsPerPage={rowsPerPage}
                    labelRowsPerPage={false}
                    labelDisplayedRows={displayNothing}
                    rowsPerPageOptions={[]}
                    ActionsComponent={SubmitButton}
                    disabled={!selectedAny}
                />
            </Card>
        </Stack>
    );
}
