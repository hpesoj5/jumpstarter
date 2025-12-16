"use client"
import { CaretLeftIcon } from "@phosphor-icons/react/dist/ssr/CaretLeft";
import IconButton from "@mui/material/IconButton";
import { useRouter } from "next/navigation";

export default function BackButton() {
    const router = useRouter();
    const returnToDashboard = () => {
        router.push("/dashboard");
    };

    return (
        <IconButton aria-label="back" onClick={() => {returnToDashboard()}}>
                <CaretLeftIcon />
        </IconButton>
    );
}
