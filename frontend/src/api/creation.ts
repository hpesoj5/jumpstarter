import { APIResponse, PhaseGeneration, DefinitionsCreate, APIRequest, ConfirmRequest } from "@/types/goals.d";
import { jwtDecode } from "jwt-decode";
export const API_URL = "http://localhost:8000";


type TokenPayload = {
    uid?: number,
    username?: string,
    exp?: number, //convert to JS date by calling new Date(exp * 1000)
    iat?: number
};

const getUserId = (): number => {
    try {
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) return -1;
        const decoded = jwtDecode<TokenPayload>(token);
        return decoded.uid ?? -1;
    } catch {
        return -1;
    }
};

export async function loadInitialState(): Promise<APIResponse> {
    const payload: APIRequest = {
        user_id: getUserId(),
        user_input: "",
    };
    const res = await fetch(`${API_URL}/create/load`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    console.log(res)
    if (!res.ok) throw new Error("Failed to load goal state");
    return res.json();
}

export async function sendUserInput(user_input: string): Promise<APIResponse> {
    const payload: APIRequest = {
        user_id: getUserId(),
        user_input,
    };
    const res = await fetch(`${API_URL}/create/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to send user input");
    return res.json();
}
  
export async function confirmPhase(confirm_obj: DefinitionsCreate | PhaseGeneration): Promise<APIResponse> {
    const payload: ConfirmRequest = {
        user_id: getUserId(),
        confirm_obj,
    };
    const res = await fetch(`${API_URL}/create/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Failed to confirm definitions/phases");
    return res.json();
  }
  
export async function submitPhaseComment(data: PhaseGeneration, comment: string): Promise<APIResponse> {
    const user_input = `The user's current phase is ${JSON.stringify(data)}. 
    They commented that "${comment}". Generate the new phases according to this.`;
  
    return sendUserInput(user_input);
}