import React from "react";
import ReactDOM from "react-dom/client";
import { CacheProvider } from "@emotion/react";
import createCache from "@emotion/cache";
import rtlPlugin from "stylis-plugin-rtl";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import "./index.css";
import App from "./App";

const theme = createTheme({
  direction: "rtl",
  palette: {
    mode: "light",
    primary: {
      main: "#0b6e4f",
    },
    secondary: {
      main: "#f2a900",
    },
    background: {
      default: "#f6f2ed",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: '"Tajawal", "Segoe UI", sans-serif',
  },
  shape: {
    borderRadius: 16,
  },
});

const rtlCache = createCache({
  key: "muirtl",
  stylisPlugins: [rtlPlugin],
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <CacheProvider value={rtlCache}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </CacheProvider>
  </React.StrictMode>
);
