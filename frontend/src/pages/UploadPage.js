import { useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Alert,
} from "@mui/material";
import UploadForm from "../components/UploadForm";
import ProgressIndicator from "../components/ProgressIndicator";
import SuccessPanel from "../components/SuccessPanel";
import PdfPreview from "../components/PdfPreview";
import {
  getMe,
  getMyProjects,
  uploadDocument,
  buildDownloadUrl,
  buildVerifyUrl,
} from "../services/api";

function UploadPage() {
  const [me, setMe] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [file, setFile] = useState(null);
  const [uploadStage, setUploadStage] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [uploadResult, setUploadResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialError, setInitialError] = useState("");
  const timersRef = useRef([]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId),
    [projects, selectedProjectId]
  );

  const clearTimers = () => {
    timersRef.current.forEach((timer) => clearTimeout(timer));
    timersRef.current = [];
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [meData, projectsData] = await Promise.all([getMe(), getMyProjects()]);
        setMe(meData);
        setProjects(projectsData);
        if (projectsData.length > 0) {
          setSelectedProjectId(projectsData[0].id);
        }
      } catch (error) {
        setInitialError("تعذر تحميل بيانات المستخدم أو المشاريع.");
      }
    };
    load();
    return () => clearTimers();
  }, []);

  const handleProjectChange = (event) => {
    setSelectedProjectId(event.target.value);
  };

  const handleFileChange = (event) => {
    const selected = event.target.files && event.target.files[0];
    if (selected && selected.type !== "application/pdf") {
      setUploadError("يرجى اختيار ملف PDF فقط.");
      event.target.value = "";
      return;
    }
    setUploadError("");
    setFile(selected || null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || !selectedProjectId || !me) {
      setUploadError("يرجى اختيار مشروع وملف PDF صالح.");
      return;
    }

    setLoading(true);
    setUploadError("");
    setUploadResult(null);
    setUploadStage("uploading");
    clearTimers();
    timersRef.current.push(setTimeout(() => setUploadStage("stamping"), 700));
    timersRef.current.push(setTimeout(() => setUploadStage("finalizing"), 1400));

    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", selectedProjectId);
    formData.append("user_id", me.id);

    try {
      const result = await uploadDocument(formData);
      clearTimers();
      setUploadStage("done");
      setUploadResult({
        serial: result.serial,
        downloadUrl: result.download_url || buildDownloadUrl(result.document_id),
        verifyUrl: result.verify_url || buildVerifyUrl(result.serial),
        projectId: result.project_id,
      });
    } catch (error) {
      clearTimers();
      setUploadStage("error");
      if (error.response && error.response.status === 403) {
        setUploadError("غير مصرح لك بالتحميل إلى هذا المشروع.");
      } else {
        setUploadError("حدث خطأ أثناء رفع الملف. حاول مرة أخرى.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!uploadResult?.serial) {
      return;
    }
    try {
      await navigator.clipboard.writeText(uploadResult.serial);
    } catch (error) {
      setUploadError("تعذر نسخ الرقم التسلسلي.");
    }
  };

  return (
    <Grid container spacing={4}>
      <Grid item xs={12}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          رفع مستند جديد
        </Typography>
        <Typography color="text.secondary">
          اختر المشروع وارفع ملف PDF ليتم ختمه والتحقق منه تلقائيا.
        </Typography>
      </Grid>

      {initialError ? (
        <Grid item xs={12}>
          <Alert severity="error">{initialError}</Alert>
        </Grid>
      ) : null}

      <Grid item xs={12} md={6}>
        <Card sx={{ borderRadius: 4, boxShadow: "0 18px 40px rgba(0,0,0,0.08)" }}>
          <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="h6">بيانات الرفع</Typography>
            {selectedProject ? (
              <Typography variant="body2" color="text.secondary">
                الجهة المالكة: {selectedProject.owner_company_name || "غير محدد"}
              </Typography>
            ) : null}
            <UploadForm
              projects={projects}
              selectedProjectId={selectedProjectId}
              onProjectChange={handleProjectChange}
              file={file}
              onFileChange={handleFileChange}
              onSubmit={handleSubmit}
              error={uploadError}
              isSubmitting={loading}
            />
            <ProgressIndicator stage={uploadStage} />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {uploadResult ? (
            <SuccessPanel
              serial={uploadResult.serial}
              downloadUrl={uploadResult.downloadUrl}
              verifyUrl={uploadResult.verifyUrl}
              onCopy={handleCopy}
            />
          ) : null}
          <PdfPreview url={uploadResult?.downloadUrl || ""} />
        </Box>
      </Grid>
    </Grid>
  );
}

export default UploadPage;
