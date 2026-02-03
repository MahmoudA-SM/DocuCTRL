import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  Typography,
} from "@mui/material";
import { getAdminUsers } from "../services/api";

function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await getAdminUsers();
        setUsers(data);
      } catch (err) {
        const message = err?.response?.data?.detail || "تعذر تحميل المستخدمين.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            جميع المستخدمين
          </Typography>
          <Typography color="text.secondary">
            عرض كامل للمستخدمين وأدوارهم وصلاحياتهم حسب المشروع.
          </Typography>
        </CardContent>
      </Card>

      {error ? <Alert severity="error">{error}</Alert> : null}
      {loading ? (
        <Typography color="text.secondary">جارٍ التحميل...</Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {users.map((user) => (
            <Card key={user.id} sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
              <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {user.email}
                </Typography>
                {user.projects && user.projects.length > 0 ? (
                  user.projects.map((project) => (
                    <Box key={`${user.id}-${project.project_id}`} sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        مشروع: {project.project_id}
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {(project.roles || []).map((role) => (
                          <Chip key={`${project.project_id}-role-${role}`} label={`Role: ${role}`} size="small" />
                        ))}
                        {(project.permissions || []).map((perm) => (
                          <Chip key={`${project.project_id}-perm-${perm}`} label={perm} size="small" />
                        ))}
                      </Box>
                      <Divider />
                    </Box>
                  ))
                ) : (
                  <Typography color="text.secondary">لا توجد مشاريع مرتبطة.</Typography>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}

export default AdminUsersPage;
