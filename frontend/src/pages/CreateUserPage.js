import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { createUser, getMyProjects, getPermissions, getRolePresets } from "../services/api";

const ROLE_OPTIONS = ["admin", "manager", "uploader", "viewer"];

function CreateUserPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [projects, setProjects] = useState([]);
  const [permissionsByProject, setPermissionsByProject] = useState({});
  const [rolePresetsByProject, setRolePresetsByProject] = useState({});
  const [assignments, setAssignments] = useState([
    { project_id: "", role_name: ROLE_OPTIONS[1], permissions: [] },
  ]);

  const loadProjectData = async (projectId) => {
    if (!projectId || permissionsByProject[projectId]) {
      return;
    }
    try {
      const [permissions, presets] = await Promise.all([
        getPermissions(projectId),
        getRolePresets(projectId),
      ]);
      setPermissionsByProject((prev) => ({ ...prev, [projectId]: permissions }));
      setRolePresetsByProject((prev) => ({ ...prev, [projectId]: presets }));
    } catch (err) {
      setError("تعذر تحميل الصلاحيات للمشروع المحدد.");
    }
  };

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await getMyProjects();
        setProjects(data);
        if (data.length > 0) {
          const firstId = data[0].id;
          setAssignments((prev) =>
            prev.map((item, index) =>
              index === 0 && !item.project_id
                ? { ...item, project_id: firstId }
                : item
            )
          );
          await loadProjectData(firstId);
        }
      } catch (err) {
        setError("تعذر تحميل المشاريع المتاحة.");
      }
    };
    loadProjects();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      setError("يرجى إدخال البريد الإلكتروني.");
      return;
    }
    if (!password || password.length < 8) {
      setError("كلمة المرور يجب أن تكون 8 أحرف على الأقل.");
      return;
    }
    if (password !== confirmPassword) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }

    const cleanedAssignments = assignments
      .map((assignment) => ({
        project_id: Number(assignment.project_id),
        role_name: assignment.role_name || null,
        permissions: assignment.permissions || [],
      }))
      .filter((assignment) => assignment.project_id && (assignment.role_name || assignment.permissions.length > 0));

    if (cleanedAssignments.length === 0) {
      setError("يجب إسناد مشروع ودور أو صلاحية واحدة على الأقل.");
      return;
    }
    const projectIds = cleanedAssignments.map((item) => item.project_id);
    const uniqueProjects = new Set(projectIds);
    if (uniqueProjects.size !== projectIds.length) {
      setError("لا يمكن تكرار نفس المشروع في الإسنادات.");
      return;
    }

    setSaving(true);
    try {
      const created = await createUser({
        email: normalizedEmail,
        password,
        assignments: cleanedAssignments,
      });
      setSuccess(`تم إنشاء المستخدم: ${created.email}`);
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      setAssignments([
        { project_id: projects[0]?.id || "", role_name: ROLE_OPTIONS[1], permissions: [] },
      ]);
    } catch (err) {
      const message = err?.response?.data?.detail || "تعذر إنشاء المستخدم.";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const applyPreset = (index, presetName) => {
    const projectId = assignments[index]?.project_id;
    if (!projectId) {
      return;
    }
    const presets = rolePresetsByProject[projectId] || [];
    const preset = presets.find((role) => role.name === presetName);
    if (!preset) {
      return;
    }
    setAssignments((prev) =>
      prev.map((item, itemIndex) =>
        itemIndex === index
          ? { ...item, permissions: preset.permissions || [] }
          : item
      )
    );
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            إضافة مستخدم جديد
          </Typography>
          <Typography color="text.secondary">
            أنشئ حسابًا جديدًا مع تحديد الدور أو الصلاحيات لكل مشروع.
          </Typography>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          {success ? <Alert severity="success">{success}</Alert> : null}
          <Box component="form" onSubmit={handleSubmit} sx={{ display: "grid", gap: 2 }}>
            <TextField
              label="البريد الإلكتروني"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              fullWidth
              required
            />
            <TextField
              label="كلمة المرور"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
              required
            />
            <TextField
              label="تأكيد كلمة المرور"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              fullWidth
              required
            />
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                تعيين المشاريع والأدوار أو الصلاحيات
              </Typography>
              {assignments.map((assignment, index) => {
                const projectId = assignment.project_id;
                const permissions = permissionsByProject[projectId] || [];
                const presets = rolePresetsByProject[projectId] || [];
                return (
                  <Box key={`${assignment.project_id}-${index}`} sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                    <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                      <FormControl sx={{ minWidth: 200, flex: 1 }}>
                        <InputLabel id={`project-label-${index}`}>المشروع</InputLabel>
                        <Select
                          labelId={`project-label-${index}`}
                          value={assignment.project_id}
                          label="المشروع"
                          onChange={async (event) => {
                            const value = event.target.value;
                            setAssignments((prev) =>
                              prev.map((item, itemIndex) =>
                                itemIndex === index
                                  ? { ...item, project_id: value, permissions: [] }
                                  : item
                              )
                            );
                            await loadProjectData(value);
                          }}
                        >
                          {projects.map((project) => (
                            <MenuItem key={project.id} value={project.id}>
                              {project.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel id={`role-label-${index}`}>الدور</InputLabel>
                        <Select
                          labelId={`role-label-${index}`}
                          value={assignment.role_name || ""}
                          label="الدور"
                          onChange={(event) => {
                            const value = event.target.value;
                            setAssignments((prev) =>
                              prev.map((item, itemIndex) =>
                                itemIndex === index
                                  ? { ...item, role_name: value }
                                  : item
                              )
                            );
                          }}
                        >
                          <MenuItem value="">بدون</MenuItem>
                          {ROLE_OPTIONS.map((role) => (
                            <MenuItem key={role} value={role}>
                              {role}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <FormControl sx={{ minWidth: 220, flex: 1 }}>
                        <InputLabel id={`preset-label-${index}`}>قالب الدور</InputLabel>
                        <Select
                          labelId={`preset-label-${index}`}
                          value={""}
                          label="قالب الدور"
                          onChange={(event) => applyPreset(index, event.target.value)}
                        >
                          <MenuItem value="">بدون</MenuItem>
                          {presets.map((preset) => (
                            <MenuItem key={preset.name} value={preset.name}>
                              {preset.description ? `${preset.name} - ${preset.description}` : preset.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Button
                        variant="outlined"
                        color="error"
                        onClick={() =>
                          setAssignments((prev) => prev.filter((_, itemIndex) => itemIndex !== index))
                        }
                        disabled={assignments.length === 1}
                      >
                        إزالة
                      </Button>
                    </Box>
                    <FormControl fullWidth>
                      <InputLabel id={`perm-label-${index}`}>الصلاحيات</InputLabel>
                      <Select
                        labelId={`perm-label-${index}`}
                        multiple
                        value={assignment.permissions || []}
                        label="الصلاحيات"
                        onChange={(event) => {
                          const value = event.target.value;
                          setAssignments((prev) =>
                            prev.map((item, itemIndex) =>
                              itemIndex === index
                                ? { ...item, permissions: value }
                                : item
                            )
                          );
                        }}
                        renderValue={(selected) => (
                          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                            {selected.map((perm) => (
                              <Chip key={perm} label={perm} size="small" />
                            ))}
                          </Box>
                        )}
                      >
                        {permissions.map((perm) => (
                          <MenuItem key={perm.name} value={perm.name}>
                            {perm.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Box>
                );
              })}
              <Button
                variant="outlined"
                onClick={() =>
                  setAssignments((prev) => [
                    ...prev,
                    { project_id: projects[0]?.id || "", role_name: ROLE_OPTIONS[1], permissions: [] },
                  ])
                }
                disabled={projects.length === 0}
              >
                إضافة مشروع
              </Button>
            </Box>
            <Button type="submit" variant="contained" disabled={saving}>
              {saving ? "جارٍ الإنشاء..." : "إضافة المستخدم"}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default CreateUserPage;
