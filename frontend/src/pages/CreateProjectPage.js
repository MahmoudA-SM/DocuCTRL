import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { createOwnerCompany, createProject, getOwnerCompanies } from "../services/api";

function CreateProjectPage() {
  const [owners, setOwners] = useState([]);
  const [ownersLoading, setOwnersLoading] = useState(false);
  const [ownerName, setOwnerName] = useState("");
  const [ownerCode, setOwnerCode] = useState("");
  const [ownerError, setOwnerError] = useState("");
  const [ownerSuccess, setOwnerSuccess] = useState("");
  const [ownerSaving, setOwnerSaving] = useState(false);

  const [projectName, setProjectName] = useState("");
  const [selectedOwnerId, setSelectedOwnerId] = useState("");
  const [projectError, setProjectError] = useState("");
  const [projectSuccess, setProjectSuccess] = useState("");
  const [projectSaving, setProjectSaving] = useState(false);

  const sortedOwners = useMemo(() => {
    return [...owners].sort((a, b) => (a.name || "").localeCompare(b.name || ""));
  }, [owners]);

  const loadOwners = async () => {
    setOwnersLoading(true);
    setOwnerError("");
    try {
      const data = await getOwnerCompanies();
      setOwners(data);
      if (!selectedOwnerId && data.length > 0) {
        setSelectedOwnerId(data[0].id);
      }
    } catch (err) {
      setOwnerError("تعذر تحميل الجهات المالكة.");
    } finally {
      setOwnersLoading(false);
    }
  };

  useEffect(() => {
    loadOwners();
  }, []);

  const handleCreateOwner = async (event) => {
    event.preventDefault();
    setOwnerError("");
    setOwnerSuccess("");
    const name = ownerName.trim();
    const code = ownerCode.trim();
    if (!name || !code) {
      setOwnerError("اسم الجهة ورمزها مطلوبان.");
      return;
    }
    setOwnerSaving(true);
    try {
      const created = await createOwnerCompany({ name, code });
      setOwners((prev) => [...prev, created]);
      setSelectedOwnerId(created.id);
      setOwnerName("");
      setOwnerCode("");
      setOwnerSuccess("تم إنشاء الجهة المالكة.");
    } catch (err) {
      const message = err?.response?.data?.detail || "تعذر إنشاء الجهة المالكة.";
      setOwnerError(message);
    } finally {
      setOwnerSaving(false);
    }
  };

  const handleCreateProject = async (event) => {
    event.preventDefault();
    setProjectError("");
    setProjectSuccess("");
    const name = projectName.trim();
    if (!name || !selectedOwnerId) {
      setProjectError("اسم المشروع والجهة المالكة مطلوبان.");
      return;
    }
    setProjectSaving(true);
    try {
      const created = await createProject({
        name,
        owner_company_id: selectedOwnerId,
      });
      setProjectName("");
      setProjectSuccess(`تم إنشاء المشروع للجهة ${created.owner_company_name || "المالكة"}.`);
    } catch (err) {
      const message = err?.response?.data?.detail || "تعذر إنشاء المشروع.";
      setProjectError(message);
    } finally {
      setProjectSaving(false);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            إنشاء جهة مالكة ومشروع
          </Typography>
          <Typography color="text.secondary">
            أضف جهة مالكة جديدة ثم أنشئ مشروعًا مرتبطًا بها.
          </Typography>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="h6">الجهة المالكة</Typography>
          {ownerError ? <Alert severity="error">{ownerError}</Alert> : null}
          {ownerSuccess ? <Alert severity="success">{ownerSuccess}</Alert> : null}
          <Box component="form" onSubmit={handleCreateOwner} sx={{ display: "grid", gap: 2 }}>
            <TextField
              label="اسم الجهة"
              value={ownerName}
              onChange={(event) => setOwnerName(event.target.value)}
              fullWidth
            />
            <TextField
              label="رمز الجهة"
              value={ownerCode}
              onChange={(event) => setOwnerCode(event.target.value)}
              helperText="يتم حفظ الرمز بحروف كبيرة."
              fullWidth
            />
            <Box sx={{ display: "flex", gap: 1 }}>
              <Button type="submit" variant="contained" disabled={ownerSaving}>
                {ownerSaving ? "جارٍ الحفظ..." : "إنشاء جهة"}
              </Button>
              <Button variant="outlined" onClick={loadOwners} disabled={ownersLoading}>
                تحديث القائمة
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="h6">المشروع</Typography>
          {projectError ? <Alert severity="error">{projectError}</Alert> : null}
          {projectSuccess ? <Alert severity="success">{projectSuccess}</Alert> : null}
          <Box component="form" onSubmit={handleCreateProject} sx={{ display: "grid", gap: 2 }}>
            <TextField
              label="اسم المشروع"
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel id="owner-select-label">الجهة المالكة</InputLabel>
              <Select
                labelId="owner-select-label"
                value={selectedOwnerId}
                label="الجهة المالكة"
                onChange={(event) => setSelectedOwnerId(event.target.value)}
                disabled={sortedOwners.length === 0}
              >
                {sortedOwners.map((owner) => (
                  <MenuItem key={owner.id} value={owner.id}>
                    {owner.name} ({owner.code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Divider />
            <Button type="submit" variant="contained" disabled={projectSaving}>
              {projectSaving ? "جارٍ الحفظ..." : "إنشاء مشروع"}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default CreateProjectPage;
