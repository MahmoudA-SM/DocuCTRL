import { Box, Typography } from "@mui/material";

function PdfPreview({ url }) {
  if (!url) {
    return (
      <Box
        sx={{
          p: 4,
          textAlign: "center",
          color: "text.secondary",
          minHeight: 320,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 2,
          border: "1px dashed var(--border)",
          backgroundColor: "#fafbfc",
        }}
      >
        <Typography variant="body2">
          لم يتم تحميل ملف PDF بعد. ستظهر المعاينة هنا.
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        borderRadius: 2,
        overflow: "hidden",
        border: "1px solid var(--border)",
        backgroundColor: "#ffffff",
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