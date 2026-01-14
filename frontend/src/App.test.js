import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders DocuCTRL header", () => {
  render(<App />);
  const heading = screen.getByText(/DocuCTRL/i);
  expect(heading).toBeInTheDocument();
});
