import { NextResponse } from "next/server";

export async function POST(req: Request) {
    const { query } = await req.json();

    const swiftUrl = process.env.NEXT_PUBLIC_SWIFT_URL || "http://localhost:8005";

    try {
        const response = await fetch(swiftUrl + "/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ query }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Create a new ReadableStream from the response data
        const stream = new ReadableStream({
            start(controller) {
                controller.enqueue(JSON.stringify(data));
                controller.close();
            }
        });

        // Set response headers and return the stream
        const headers = new Headers();
        headers.set("Content-Type", "application/json");
        return new Response(stream, { headers });
    } catch (error) {
        console.error("Error:", error);
        return NextResponse.json({ error: 'An error occurred while processing your request.' }, { status: 500 });
    }
}