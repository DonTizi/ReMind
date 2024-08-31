import { StreamingTextResponse, Message } from "ai";
import { NextResponse } from "next/server";

export const runtime = "edge";
export const dynamic = "force-dynamic";

interface ServerResponse {
  status: string;
  results: string[];
  message?: string;
}

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1];

  try {
    const response = await fetch('http://localhost:8005/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: lastMessage.content }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Server response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const data: ServerResponse = await response.json();

    if (data.status === "error") {
      throw new Error(data.message || "Unknown error occurred");
    }

    if (!data.results || !Array.isArray(data.results) || data.results.length === 0) {
      throw new Error('Invalid response format from server');
    }

    const aiResponse = data.results[0];

    // Create a ReadableStream from the AI response
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(aiResponse));
        controller.close();
      },
    });

    return new StreamingTextResponse(stream);
  } catch (error: unknown) {
    console.error('Error:', error);
    let errorMessage = 'An error occurred while processing your request.';
    
    if (error instanceof Error) {
      errorMessage = error.message;
    }

    return new Response(JSON.stringify({ error: errorMessage }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}