import { useState } from "react";
import { Alert, Box, Button, Card, CardContent, TextField, Typography } from "@mui/material";
import { createUser } from "../services/api";

function CreateUserPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

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

    setSaving(true);
    try {
      const created = await createUser({ email: normalizedEmail, password });
      setSuccess(`تم إنشاء المستخدم: ${created.email}`);
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      const message = err?.response?.data?.detail || "تعذر إنشاء المستخدم.";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            إضافة مستخدم جديد
          </Typography>
          <Typography color="text.secondary">
            أنشئ حساباً جديداً ليتمكن المستخدم من الدخول إلى النظام.
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
