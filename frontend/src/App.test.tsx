import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App navigation", () => {
  it("switches between Command Map and Ingest Log via header tabs", async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByText("Export PDF Summary")).toBeInTheDocument();
    await user.click(screen.getByText("Ingest Log"));
    expect(screen.getByText(/INGEST LOG — OPERATOR VIEW/)).toBeInTheDocument();
    await user.click(screen.getByText("Command Map"));
    expect(screen.getByText("Export PDF Summary")).toBeInTheDocument();
  });

  it("link pill navigates to error-state, retry returns to dashboard with a toast", async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByText("Export PDF Summary")).toBeInTheDocument();
    await user.click(screen.getByTitle("click to simulate link status"));
    expect(screen.getByText(/CONNECTION LOST/)).toBeInTheDocument();
    await user.click(screen.getByText("Retry Connection"));
    expect(await screen.findByText("Export PDF Summary")).toBeInTheDocument();
    expect(screen.getByText("Connection restored.")).toBeInTheDocument();
  });
});
