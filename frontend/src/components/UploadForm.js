import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  Alert,
} from "@mui/material";

function UploadForm({
  projects,
  selectedProjectId,
  onProjectChange,
  file,
  onFileChange,
  onSubmit,
  error,
  isSubmitting,
}) {
  return (
    <Box
      component="form"
      onSubmit={onSubmit}
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      {error ? <Alert severity="error">{error}</Alert> : null}
      <FormControl fullWidth>
        <InputLabel id="project-select-label">المشروع</InputLabel>
        <Select
          labelId="project-select-label"
          value={selectedProjectId}
          label="المشروع"
          onChange={onProjectChange}
          disabled={projects.length === 0}
        >
          {projects.map((project) => (
            <MenuItem key={project.id} value={project.id}>
              {project.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
        <Button variant="outlined" component="label">
          اختيار ملف PDF
          <input
            hidden
            type="file"
            accept="application/pdf"
            onChange={onFileChange}
          />
        </Button>
        <Typography variant="body2" color="text.secondary">
          {file ? file.name : "لم يتم اختيار ملف بعد"}
        </Typography>
      </Box>

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={!selectedProjectId || !file || isSubmitting}
      >
        رفع المستند
      </Button>
    </Box>
  );
}

export default UploadForm;
