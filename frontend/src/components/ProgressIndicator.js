import { Box, CircularProgress, Typography } from "@mui/material";

const labels = {
  uploading: "جاري رفع الملف",
  stamping: "جاري ختم الوثيقة",
  finalizing: "جاري تجهيز البيانات",
};

function ProgressIndicator({ stage }) {
  if (!stage || stage === "done") {
    return null;
  }

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
      <CircularProgress size={24} />
      <Typography variant="body1" color="text.secondary">
        {labels[stage] || "جاري المعالجة"}
      </Typography>
    </Box>
  );
}

export default ProgressIndicator;
