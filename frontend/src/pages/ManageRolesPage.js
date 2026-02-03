import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import {
  getMyProjects,
  getPermissions,
  getRolePresets,
  getUserPermissionsForProject,
  getVisibleUsers,
  setUserPermissionsForProject,
} from "../services/api";

function groupByResource(permissions) {
  return permissions.reduce((acc, perm) => {
    const key = perm.resource || "other";
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(perm);
    return acc;
  }, {});
}

function ManageRolesPage() {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [rolePresets, setRolePresets] = useState([]);
  const [selection, setSelection] = useState({
    projectId: "",
    userId: "",
    preset: "",
  });
  const [directPermissions, setDirectPermissions] = useState([]);
  const [effectivePermissions, setEffectivePermissions] = useState([]);
  const [checked, setChecked] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const groupedPermissions = useMemo(() => groupByResource(permissions), [permissions]);

  const loadBaseData = async () => {
    setLoading(true);
    setError("");
    try {
      const projectsData = await getMyProjects();
      setProjects(projectsData);
      const initialProjectId =
        selection.projectId || (projectsData.length > 0 ? projectsData[0].id : "");
      if (initialProjectId) {
        const [permissionsData, presetsData] = await Promise.all([
          getPermissions(initialProjectId),
          getRolePresets(initialProjectId),
        ]);
        setPermissions(permissionsData);
        setRolePresets(presetsData);
      } else {
        setPermissions([]);
        setRolePresets([]);
      }
      if (projectsData.length > 0 && !selection.projectId) {
        setSelection((prev) => ({ ...prev, projectId: projectsData[0].id }));
      }
    } catch (err) {
      setError("تعذر تحميل البيانات الأساسية.");
    } finally {
      setLoading(false);
    }
  };

  const loadUsersForProject = async (projectId) => {
    if (!projectId) {
      setUsers([]);
      return;
    }
    try {
      const [usersData, permissionsData, presetsData] = await Promise.all([
        getVisibleUsers(projectId),
        getPermissions(projectId),
        getRolePresets(projectId),
      ]);
      setUsers(usersData);
      setPermissions(permissionsData);
      setRolePresets(presetsData);
      if (usersData.length > 0) {
        setSelection((prev) => ({ ...prev, userId: usersData[0].id }));
      } else {
        setSelection((prev) => ({ ...prev, userId: "" }));
      }
    } catch (err) {
      setError("تعذر تحميل المستخدمين لهذا المشروع.");
    }
  };

  const loadUserPermissions = async (projectId, userId) => {
    if (!projectId || !userId) {
      setDirectPermissions([]);
      setEffectivePermissions([]);
      setChecked(new Set());
      return;
    }
    try {
      const data = await getUserPermissionsForProject({ projectId, userId });
      setDirectPermissions(data.direct_permissions || []);
      setEffectivePermissions(data.effective_permissions || []);
      setChecked(new Set(data.direct_permissions || []));
    } catch (err) {
      setError("تعذر تحميل صلاحيات المستخدم.");
    }
  };

  useEffect(() => {
    loadBaseData();
  }, []);

  useEffect(() => {
    if (selection.projectId) {
      loadUsersForProject(selection.projectId);
    }
  }, [selection.projectId]);

  useEffect(() => {
    if (selection.projectId && selection.userId) {
      loadUserPermissions(selection.projectId, selection.userId);
    }
  }, [selection.projectId, selection.userId]);

  const handleTogglePermission = (permName) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(permName)) {
        next.delete(permName);
      } else {
        next.add(permName);
      }
      return next;
    });
  };

  const handleApplyPreset = () => {
    if (!selection.preset) {
      return;
    }
    const preset = rolePresets.find((role) => role.name === selection.preset);
    if (!preset) {
      return;
    }
    setChecked(new Set(preset.permissions || []));
  };

  const handleSave = async () => {
    setError("");
    setSuccess("");
    if (!selection.projectId || !selection.userId) {
      setError("اختر مشروعًا ومستخدمًا أولاً.");
      return;
    }
    try {
      await setUserPermissionsForProject({
        projectId: selection.projectId,
        userId: selection.userId,
        permissions: Array.from(checked),
      });
      setSuccess("تم حفظ الصلاحيات.");
      await loadUserPermissions(selection.projectId, selection.userId);
    } catch (err) {
      const message = err?.response?.data?.detail || "تعذر حفظ الصلاحيات.";
      setError(message);
    }
  };

  const selectedUser = users.find((user) => String(user.id) === String(selection.userId));

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            إدارة الصلاحيات
          </Typography>
          <Typography color="text.secondary">
            اختر المشروع والمستخدم ثم حدّد الصلاحيات يدويًا، مع إمكانية تطبيق قالب دور.
          </Typography>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          {success ? <Alert severity="success">{success}</Alert> : null}

          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <FormControl fullWidth>
              <InputLabel id="project-select-label">المشروع</InputLabel>
              <Select
                labelId="project-select-label"
                value={selection.projectId}
                label="المشروع"
                onChange={(event) =>
                  setSelection((prev) => ({ ...prev, projectId: event.target.value }))
                }
              >
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="user-select-label">المستخدم</InputLabel>
              <Select
                labelId="user-select-label"
                value={selection.userId}
                label="المستخدم"
                onChange={(event) =>
                  setSelection((prev) => ({ ...prev, userId: event.target.value }))
                }
              >
                {users.map((user) => (
                  <MenuItem key={user.id} value={user.id}>
                    {user.email}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel id="preset-select-label">قالب الدور</InputLabel>
              <Select
                labelId="preset-select-label"
                value={selection.preset}
                label="قالب الدور"
                onChange={(event) =>
                  setSelection((prev) => ({ ...prev, preset: event.target.value }))
                }
              /*
This is a
multi‑line comment.
*/
              >
                <MenuItem value="">بدون</MenuItem>
                {rolePresets.map((role) => (
                  <MenuItem key={role.name} value={role.name}>
                    {role.description ? `${role.name} - ${role.description}` : role.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Button variant="outlined" onClick={handleApplyPreset} disabled={!selection.preset}>
              تطبيق القالب
            </Button>
            <Button variant="contained" onClick={handleSave} disabled={loading}>
              حفظ الصلاحيات
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="h6">الصلاحيات المتاحة</Typography>
          {permissions.length === 0 ? (
            <Typography color="text.secondary">لا توجد صلاحيات متاحة.</Typography>
          ) : (
            Object.entries(groupedPermissions).map(([resource, perms]) => (
              <Box key={resource} sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  {resource}
                </Typography>
                <FormGroup row>
                  {perms.map((perm) => (
                    <FormControlLabel
                      key={perm.name}
                      control={
                        <Checkbox
                          checked={checked.has(perm.name)}
                          onChange={() => handleTogglePermission(perm.name)}
                        />
                      }
                      label={perm.name}
                    />
                  ))}
                </FormGroup>
                <Divider />
              </Box>
            ))
          )}
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="h6">ملخص المستخدم</Typography>
          {!selectedUser ? (
            <Typography color="text.secondary">اختر مستخدمًا لعرض الملخص.</Typography>
          ) : (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Typography>{selectedUser.email}</Typography>
              <Typography color="text.secondary">
                صلاحيات مباشرة: {directPermissions.length}
              </Typography>
              <Typography color="text.secondary">
                صلاحيات فعّالة (تشمل الأدوار): {effectivePermissions.length}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default ManageRolesPage;
