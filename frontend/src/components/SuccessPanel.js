import { Box, Button, Chip, Typography } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

function SuccessPanel({ serial, downloadUrl, verifyUrl, onCopy }) {
  return (
    <Box
      sx={{
        backgroundColor: "rgba(255, 255, 255, 0.9)",
        borderRadius: 3,
        p: 3,
        boxShadow: "0 20px 40px rgba(0,0,0,0.08)",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <CheckCircleIcon color="success" />
        <Typography variant="h6">تم رفع المستند بنجاح</Typography>
      </Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
        <Chip label={`الرقم التسلسلي: ${serial}`} color="secondary" />
        <Button
          variant="text"
          size="small"
          startIcon={<ContentCopyIcon />}
          onClick={onCopy}
        >
          نسخ الرقم
        </Button>
      </Box>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
        <Button variant="contained" href={downloadUrl} target="_blank">
          تنزيل الملف
        </Button>
        <Button variant="outlined" href={verifyUrl} target="_blank">
          التحقق من المستند
        </Button>
      </Box>
    </Box>
  );
}

export default SuccessPanel;
