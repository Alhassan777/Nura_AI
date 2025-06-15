import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    {
      error: "This endpoint has been moved to the backend API",
      message: "Please use the backend user endpoints instead",
      backend_url: `${process.env.NEXT_PUBLIC_API_URL}/users/profile`,
      documentation: "See backend API documentation for available endpoints",
    },
    { status: 410 } // Gone
  );
}
