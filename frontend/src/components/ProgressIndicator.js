import { Box, CircularProgress, Typography } from "@mui/material";

const labels = {
  uploading: "جاري رفع الملف",
  stamping: "جاري ختم المستند",
  finalizing: "جاري تجهيز الروابط",
};

function ProgressIndicator({ stage }) {
  if (!stage || stage === "done") {
    return null;
  }

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
      <CircularProgress size={20} />
      <Typography variant="body2" color="text.secondary">
        {labels[stage] || "جاري المعالجة"}
      </Typography>
    </Box>
  );
}

export default ProgressIndicator;
