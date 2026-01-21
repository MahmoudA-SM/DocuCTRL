import { Box, Button, Chip, Typography } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

function SuccessPanel({ serial, downloadUrl, verifyUrl, onCopy }) {
  return (
    <Box
      sx={{
        backgroundColor: "var(--panel)",
        borderRadius: 2,
        p: 3,
        border: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <CheckCircleIcon color="success" />
        <Typography variant="h6">تم إصدار المستند بنجاح</Typography>
      </Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
        <Chip label={`رقم التسلسل: ${serial}`} color="secondary" />
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
          تنزيل المستند
        </Button>
        <Button variant="outlined" href={verifyUrl} target="_blank">
          التحقق من المستند
        </Button>
      </Box>
    </Box>
  );
}

export default SuccessPanel;
