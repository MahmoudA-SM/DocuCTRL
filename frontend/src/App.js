import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import { Box, Container, Typography, Button, IconButton } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import QrCodeScannerIcon from "@mui/icons-material/QrCodeScanner";
import AddBusinessIcon from "@mui/icons-material/AddBusiness";
import PersonAddAltIcon from "@mui/icons-material/PersonAddAlt";
import UploadPage from "./pages/UploadPage";
import DocumentListPage from "./pages/DocumentListPage";
import VerifyPage from "./pages/VerifyPage";
import CreateProjectPage from "./pages/CreateProjectPage";
import CreateUserPage from "./pages/CreateUserPage";
import ManageRolesPage from "./pages/ManageRolesPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import { getMe } from "./services/api";

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [me, setMe] = useState(null);
  const sidebarWidth = sidebarCollapsed ? 84 : 260;

  useEffect(() => {
    const ensureAuth = async () => {
      if (window.location.pathname === "/login") {
        setAuthChecked(true);
        return;
      }
      const url = new URL(window.location.href);
      const urlToken = url.searchParams.get("access_token");
      if (urlToken) {
        try {
          localStorage.setItem("access_token", urlToken);
        } catch (err) {
        }
        url.searchParams.delete("access_token");
        window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
      }
      const token = localStorage.getItem("access_token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      setAuthChecked(true);
      try {
        const meData = await getMe();
        setMe(meData);
      } catch (err) {
        try {
          localStorage.removeItem("access_token");
        } catch (removeErr) {
        }
        window.location.href = "/login";
      }
    };
    ensureAuth();
  }, []);

  if (!authChecked) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "var(--bg)",
        }}
      >
        <Typography color="text.secondary">جاري التحميل...</Typography>
      </Box>
    );
  }

  const canManageUsers = true;
  const canManageProjects = true;
  const canUpload = true;
  const canViewDocuments = true;
  const canVerify = true;

  const toggleLabel = sidebarCollapsed ? "توسيع الشريط الجانبي" : "طي الشريط الجانبي";

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
              aria-label={toggleLabel}
            >
              <MenuIcon fontSize="small" />
            </IconButton>
          </Box>
          {!sidebarCollapsed ? (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              لوحة تحكم لإدارة ملفات PDF والمشروعات بأمان كامل.
            </Typography>
          ) : null}
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {canUpload ? (
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
            ) : null}
            {canViewDocuments ? (
              <Button
                component={Link}
                to="/documents"
                variant="outlined"
                fullWidth
                startIcon={<FolderOpenOutlinedIcon />}
                title={sidebarCollapsed ? "المستندات" : undefined}
                aria-label={sidebarCollapsed ? "المستندات" : undefined}
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
                {sidebarCollapsed ? "" : "المستندات"}
              </Button>
            ) : null}
            {canManageProjects ? (
              <Button
                component={Link}
                to="/projects/new"
                variant="outlined"
                fullWidth
                startIcon={<AddBusinessIcon />}
                title={sidebarCollapsed ? "إنشاء مشروع" : undefined}
                aria-label={sidebarCollapsed ? "إنشاء مشروع" : undefined}
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
                {sidebarCollapsed ? "" : "إنشاء مشروع"}
              </Button>
            ) : null}
            {canManageUsers ? (
              <Button
                component={Link}
                to="/users/new"
                variant="outlined"
                fullWidth
                startIcon={<PersonAddAltIcon />}
                title={sidebarCollapsed ? "إضافة مستخدم" : undefined}
                aria-label={sidebarCollapsed ? "إضافة مستخدم" : undefined}
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
                {sidebarCollapsed ? "" : "إضافة مستخدم"}
              </Button>
            ) : null}
            {canManageUsers ? (
              <Button
                component={Link}
                to="/admin/users"
                variant="outlined"
                fullWidth
                startIcon={<PersonAddAltIcon />}
                title={sidebarCollapsed ? "جميع المستخدمين" : undefined}
                aria-label={sidebarCollapsed ? "جميع المستخدمين" : undefined}
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
                {sidebarCollapsed ? "" : "جميع المستخدمين"}
              </Button>
            ) : null}
            {canManageUsers ? (
              <Button
                component={Link}
                to="/roles"
                variant="outlined"
                fullWidth
                startIcon={<PersonAddAltIcon />}
                title={sidebarCollapsed ? "إدارة الصلاحيات" : undefined}
                aria-label={sidebarCollapsed ? "إدارة الصلاحيات" : undefined}
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
                {sidebarCollapsed ? "" : "إدارة الصلاحيات"}
              </Button>
            ) : null}
            {canVerify ? (
              <Button
                component={Link}
                to="/verify"
                variant="text"
                fullWidth
                startIcon={<QrCodeScannerIcon />}
                title={sidebarCollapsed ? "التحقق من مستند" : undefined}
                aria-label={sidebarCollapsed ? "التحقق من مستند" : undefined}
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
                {sidebarCollapsed ? "" : "التحقق من مستند"}
              </Button>
            ) : null}
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
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, flexWrap: "wrap" }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    لوحة التحكم
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    تابع عمليات الرفع والتحقق وإدارة المشروعات من مكان واحد.
                  </Typography>
                </Box>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                </Box>
              </Box>
            </Container>
          </Box>

          <Container maxWidth="xl" sx={{ py: 4 }}>
            <Routes>
              <Route path="/" element={<Navigate to="/upload" replace />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/projects/new" element={<CreateProjectPage />} />
              <Route path="/documents" element={<DocumentListPage />} />
              <Route path="/projects/:projectId/documents" element={<DocumentListPage />} />
              <Route path="/users/new" element={<CreateUserPage />} />
              <Route path="/admin/users" element={<AdminUsersPage />} />
              <Route path="/roles" element={<ManageRolesPage />} />
              <Route path="/verify" element={<VerifyPage />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </BrowserRouter>
  );
}

export default App;
