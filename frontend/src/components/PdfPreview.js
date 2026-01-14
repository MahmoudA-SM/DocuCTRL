import { Box, Typography } from "@mui/material";

function PdfPreview({ url }) {
  if (!url) {
    return (
      <Box sx={{ p: 3, textAlign: "center", color: "text.secondary" }}>
        <Typography variant="body2">معاينة الـ PDF ستظهر هنا بعد الرفع</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        borderRadius: 3,
        overflow: "hidden",
        border: "1px solid rgba(0,0,0,0.08)",
        minHeight: 420,
      }}
    >
      <iframe
        title="معاينة المستند"
        src={url}
        style={{ width: "100%", height: "100%", minHeight: 420, border: "none" }}
      />
    </Box>
  );
}

export default PdfPreview;
