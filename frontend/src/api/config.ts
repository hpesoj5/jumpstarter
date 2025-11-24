export const API_URL = "http://localhost:8000";

export type TokenPayload = {
    uid?: number;
    username?: string;
    exp?: number; //convert to JS date by calling new Date(exp * 1000)
    iat?: number;
};
