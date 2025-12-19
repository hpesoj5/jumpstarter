import "@/styles/globals.css";

export const metadata = {
    title: "JumpStarter",
    description: "Build Your Tomorrow, Today",
};

export default function RootLayout(
    { children, }:
    { children: React.ReactNode; }) {
    return (
        <html lang="en">
            <body className="flex flex-row h-screen bg-gray-50 text-gray-900">
                {children}
            </body>
        </html>
    );
}
