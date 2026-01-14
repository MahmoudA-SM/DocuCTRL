import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Box, Container, Typography, Button } from "@mui/material";
import UploadPage from "./pages/UploadPage";
import DocumentListPage from "./pages/DocumentListPage";

function App() {
  return (
    <BrowserRouter>
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          overflow: "hidden",
          "&::before": {
            content: '""',
            position: "absolute",
            inset: "-20% -10%",
            background:
              "radial-gradient(circle at 20% 20%, rgba(242, 169, 0, 0.25), transparent 55%), radial-gradient(circle at 80% 15%, rgba(11, 110, 79, 0.18), transparent 50%), radial-gradient(circle at 50% 85%, rgba(33, 150, 243, 0.12), transparent 55%)",
            zIndex: 0,
          },
        }}
      >
        <Box
          sx={{
            position: "relative",
            zIndex: 1,
            py: { xs: 4, md: 6 },
          }}
        >
          <Container maxWidth="lg">
            <Box
              sx={{
                display: "flex",
                alignItems: { xs: "flex-start", md: "center" },
                justifyContent: "space-between",
                gap: 2,
                flexDirection: { xs: "column", md: "row" },
              }}
            >
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  DocuCTRL
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                  منصة موثوقة لختم الوثائق والتحقق منها
                </Typography>
              </Box>
              <Box sx={{ display: "flex", gap: 1 }}>
                <Button variant="contained" href="/upload">
                  رفع مستند
                </Button>
              </Box>
            </Box>
          </Container>
        </Box>

        <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1, pb: 6 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/projects/:projectId/documents" element={<DocumentListPage />} />
          </Routes>
        </Container>
      </Box>
    </BrowserRouter>
  );
}

export default App;
