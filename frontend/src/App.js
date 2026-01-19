import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import { Box, Container, Typography, Button, IconButton } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import QrCodeScannerIcon from "@mui/icons-material/QrCodeScanner";
import UploadPage from "./pages/UploadPage";
import DocumentListPage from "./pages/DocumentListPage";
import VerifyPage from "./pages/VerifyPage";

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const sidebarWidth = sidebarCollapsed ? 84 : 260;

  return (
    <BrowserRouter>
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: { xs: "column", md: "row" },
          backgroundColor: "var(--bg)",
        }}
      >
        <Box
          sx={{
            width: { xs: "100%", md: sidebarWidth },
            order: { xs: 0, md: 0 },
            borderLeft: { xs: "none", md: "1px solid var(--border)" },
            borderBottom: { xs: "1px solid var(--border)", md: "none" },
            backgroundColor: "var(--panel)",
            p: 3,
            transition: "width 200ms ease",
            overflow: "hidden",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {sidebarCollapsed ? "DC" : "DocuCTRL"}
            </Typography>
            <IconButton
              size="small"
              onClick={() => setSidebarCollapsed((prev) => !prev)}
              aria-label={sidebarCollapsed ? "توسيع الشريط الجانبي" : "طي الشريط الجانبي"}
            >
              <MenuIcon fontSize="small" />
            </IconButton>
          </Box>
          {!sidebarCollapsed ? (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              نظام التحكم في المستندات لختم ملفات PDF وتتبعها.
            </Typography>
          ) : null}
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            <Button
              component={Link}
              to="/upload"
              variant="contained"
              fullWidth
              startIcon={<UploadFileOutlinedIcon />}
              title={sidebarCollapsed ? "رفع مستند" : undefined}
              aria-label={sidebarCollapsed ? "رفع مستند" : undefined}
              sx={{
                justifyContent: sidebarCollapsed ? "center" : "flex-start",
                px: sidebarCollapsed ? 1 : 2,
                minWidth: sidebarCollapsed ? 44 : "auto",
                height: sidebarCollapsed ? 44 : "auto",
                borderRadius: sidebarCollapsed ? 2.5 : 1.5,
                "& .MuiButton-startIcon": {
                  margin: 0,
                },
              }}
            >
              {sidebarCollapsed ? "" : "رفع مستند"}
            </Button>
            <Button
              component={Link}
              to="/projects/1/documents"
              variant="outlined"
              fullWidth
              startIcon={<FolderOpenOutlinedIcon />}
              title={sidebarCollapsed ? "مستندات المشاريع" : undefined}
              aria-label={sidebarCollapsed ? "مستندات المشاريع" : undefined}
              sx={{
                justifyContent: sidebarCollapsed ? "center" : "flex-start",
                px: sidebarCollapsed ? 1 : 2,
                minWidth: sidebarCollapsed ? 44 : "auto",
                height: sidebarCollapsed ? 44 : "auto",
                borderRadius: sidebarCollapsed ? 2.5 : 1.5,
                "& .MuiButton-startIcon": {
                  margin: 0,
                },
              }}
            >
              {sidebarCollapsed ? "" : "مستندات المشاريع"}
            </Button>
            <Button
              component={Link}
              to="/verify"
              variant="text"
              fullWidth
              startIcon={<QrCodeScannerIcon />}
              title={sidebarCollapsed ? "تحقق من مستند" : undefined}
              aria-label={sidebarCollapsed ? "تحقق من مستند" : undefined}
              sx={{
                justifyContent: sidebarCollapsed ? "center" : "flex-start",
                px: sidebarCollapsed ? 1 : 2,
                minWidth: sidebarCollapsed ? 44 : "auto",
                height: sidebarCollapsed ? 44 : "auto",
                borderRadius: sidebarCollapsed ? 2.5 : 1.5,
                "& .MuiButton-startIcon": {
                  margin: 0,
                },
              }}
            >
              {sidebarCollapsed ? "" : "تحقق من مستند"}
            </Button>
          </Box>
        </Box>

        <Box sx={{ flex: 1, order: { xs: 1, md: 1 } }}>
          <Box
            sx={{
              borderBottom: "1px solid var(--border)",
              backgroundColor: "var(--panel)",
            }}
          >
            <Container maxWidth="xl" sx={{ py: 2.5 }}>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    إدارة المستندات
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    تابع الرفع والتحقق في مكان واحد.
                  </Typography>
                </Box>
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Button variant="outlined" href="/verify">
                    تحقق من مستند
                  </Button>
                  <Button variant="contained" href="/upload">
                    رفع مستند
                  </Button>
                </Box>
              </Box>
            </Container>
          </Box>

          <Container maxWidth="xl" sx={{ py: 4 }}>
            <Routes>
              <Route path="/" element={<Navigate to="/upload" replace />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/projects/:projectId/documents" element={<DocumentListPage />} />
              <Route path="/verify" element={<VerifyPage />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </BrowserRouter>
  );
}

export default App;
