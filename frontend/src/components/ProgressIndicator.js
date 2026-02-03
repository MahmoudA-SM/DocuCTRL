import { Box, CircularProgress, Typography } from "@mui/material";

const labels = {
  uploading: "جارٍ رفع الملف",
  stamping: "جارٍ ختم الملف",
  finalizing: "جارٍ إنهاء العملية",
};

function ProgressIndicator({ stage }) {
  if (!stage || stage === "done") {
    return null;
  }

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
      <CircularProgress size={20} />
      <Typography variant="body2" color="text.secondary">
        {labels[stage] || "جارٍ المعالجة..."}
      </Typography>
    </Box>
  );
}

export default ProgressIndicator;