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
      main: "#1f4d7a",
    },
    secondary: {
      main: "#64748b",
    },
    background: {
      default: "#f5f6f8",
      paper: "#ffffff",
    },
    text: {
      primary: "#1f2937",
      secondary: "#5b6777",
    },
    divider: "#e3e7ee",
  },
  typography: {
    fontFamily: '"Readex Pro", "Tajawal", sans-serif',
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: "none",
        },
      },
    },
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
