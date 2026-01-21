import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  getMyProjects,
  getProjectDocuments,
  downloadDocument,
} from "../services/api";

function DocumentListPage() {
  const { projectId } = useParams();
  const [documents, setDocuments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [docs, projectList] = await Promise.all([
          getProjectDocuments(projectId),
          getMyProjects(),
        ]);
        const sortedDocs = [...docs].sort((a, b) =>
          (b.upload_date || "").localeCompare(a.upload_date || "")
        );
        setDocuments(sortedDocs);
        setProjects(projectList);
      } catch (err) {
        if (err.response && err.response.status === 403) {
          setError("ليس لديك صلاحية لعرض مستندات هذا المشروع.");
        } else {
          setError("تعذر تحميل المستندات.");
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [projectId]);

  const projectName = useMemo(() => {
    const project = projects.find((item) => String(item.id) === String(projectId));
    return project ? project.name : `مشروع رقم ${projectId}`;
  }, [projects, projectId]);

  const handleDownload = async (documentId) => {
    setDownloadingId(documentId);
    setError("");
    try {
      const blob = await downloadDocument(documentId);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener");
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch (err) {
      setError("تعذر تنزيل المستند.");
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            مستندات {projectName}
          </Typography>
          <Typography color="text.secondary">
            عرض أحدث المستندات لهذا المشروع.
          </Typography>
          <Button component={Link} to="/upload" variant="contained" sx={{ alignSelf: "flex-start" }}>
            رفع مستند جديد
          </Button>
        </CardContent>
      </Card>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent>
          {loading ? (
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <CircularProgress size={22} />
              <Typography color="text.secondary">جارٍ تحميل المستندات...</Typography>
            </Box>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>الرقم التسلسلي</TableCell>
                  <TableCell>اسم الملف</TableCell>
                  <TableCell>تاريخ الرفع</TableCell>
                  <TableCell align="left">الإجراءات</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      لا توجد مستندات بعد.
                    </TableCell>
                  </TableRow>
                ) : (
                  documents.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>{doc.serial}</TableCell>
                      <TableCell>{doc.filename}</TableCell>
                      <TableCell>
                        {doc.upload_date
                          ? new Date(doc.upload_date).toLocaleString("ar")
                          : "-"}
                      </TableCell>
                      <TableCell align="left">
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => handleDownload(doc.id)}
                          disabled={downloadingId === doc.id}
                        >
                          تنزيل
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default DocumentListPage;
