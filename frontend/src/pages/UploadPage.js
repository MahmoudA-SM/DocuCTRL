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
  downloadDocument,
  buildVerifyPageUrl,
} from "../services/api";

const stageText = {
  uploading: "جارٍ رفع الملف",
  stamping: "جارٍ ختم الملف",
  finalizing: "جارٍ إنهاء العملية",
};

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
  const [downloadUrl, setDownloadUrl] = useState("");
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
        setInitialError("تعذر تحميل البيانات من الخادم.");
      }
    };
    load();
    return () => clearTimers();
  }, []);

  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
    };
  }, [downloadUrl]);

  const handleProjectChange = (event) => {
    setSelectedProjectId(event.target.value);
  };

  const handleFileChange = (event) => {
    const selected = event.target.files && event.target.files[0];
    const fileType = selected?.type || "";
    const fileName = selected?.name || "";
    const isPdf =
      fileName.toLowerCase().endsWith(".pdf") ||
      fileType === "application/pdf" ||
      fileType === "application/x-pdf" ||
      fileType === "application/octet-stream";
    if (selected && !isPdf) {
      setUploadError("يسمح فقط بملفات PDF.");
      event.target.value = "";
      return;
    }
    setUploadError("");
    setFile(selected || null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || !selectedProjectId || !me) {
      setUploadError("يرجى اختيار ملف PDF ومشروع.");
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
      let blobUrl = "";
      try {
        const blob = await downloadDocument(result.document_id);
        blobUrl = URL.createObjectURL(blob);
        setDownloadUrl(blobUrl);
      } catch (err) {
        setDownloadUrl("");
      }
      setUploadResult({
        serial: result.serial,
        downloadUrl: blobUrl,
        verifyUrl: buildVerifyPageUrl(result.serial),
        projectId: result.project_id,
      });
    } catch (error) {
      clearTimers();
      setUploadStage("error");
      if (error.response && error.response.status === 403) {
        setUploadError("ليس لديك صلاحية لرفع المستند لهذا المشروع.");
      } else {
        const detail = error?.response?.data?.detail;
        const detailMap = {
          "Only PDF files are accepted": "يسمح فقط بملفات PDF.",
          "Project not found": "تعذر العثور على المشروع المحدد.",
          "Owner Company not found": "تعذر العثور على الجهة المالكة.",
          "Owner company does not match project owner": "الجهة المالكة لا تطابق مالك المشروع.",
          "يسمح فقط بملفات PDF.": "يسمح فقط بملفات PDF.",
        };
        if (typeof detail === "string" && detailMap[detail]) {
          setUploadError(detailMap[detail]);
        } else {
          setUploadError("تعذر رفع المستند. حاول مرة أخرى.");
        }
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
      setUploadError("تعذر نسخ الرقم إلى الحافظة.");
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {initialError ? <Alert severity="error">{initialError}</Alert> : null}

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            رفع مستند جديد
          </Typography>
          <Typography color="text.secondary">
            ارفع ملف PDF ليتم ختمه وإصداره.
          </Typography>
        </CardContent>
      </Card>

      <Grid container spacing={{ xs: 3, md: 3 }} alignItems="stretch">
        <Grid item xs={12} md={5}>
          <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
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
              {uploadStage && uploadStage !== "done" ? (
                <Box
                  sx={{
                    mt: 1,
                    p: 1.5,
                    borderRadius: 2,
                    border: "1px solid var(--border)",
                    backgroundColor: "#fafbfc",
                  }}
                >
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {stageText[uploadStage] || "جارٍ المعالجة..."}
                  </Typography>
                  <ProgressIndicator stage={uploadStage} />
                </Box>
              ) : null}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3, height: "100%" }}>
            {uploadResult ? (
              <SuccessPanel
                serial={uploadResult.serial}
                downloadUrl={uploadResult.downloadUrl}
                verifyUrl={uploadResult.verifyUrl}
                onCopy={handleCopy}
              />
            ) : (
              <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    لا توجد نتيجة بعد
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ستظهر روابط التحقق والتنزيل بعد اكتمال الرفع.
                  </Typography>
                </CardContent>
              </Card>
            )}
            <PdfPreview url={uploadResult?.downloadUrl || ""} />
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}

export default UploadPage;
