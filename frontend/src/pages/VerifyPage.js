import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
} from "@mui/material";
import jsQR from "jsqr";
import CloseIcon from "@mui/icons-material/Close";
import { downloadDocument, verifySerial } from "../services/api";

function VerifyPage() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const useJsQrRef = useRef(false);
  const rafRef = useRef(null);
  const [searchParams] = useSearchParams();

  const [serial, setSerial] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [verifiedDocumentId, setVerifiedDocumentId] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const stopCamera = () => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const normalizeSerial = (value) => {
    if (!value) {
      return "";
    }
    const trimmed = value.trim();
    const verifyIndex = trimmed.lastIndexOf("/verify/");
    if (verifyIndex !== -1) {
      const after = trimmed.slice(verifyIndex + "/verify/".length);
      return after.split(/[?#\s]/)[0];
    }
    return trimmed.split(/\s/)[0];
  };

  const handleVerify = async (value) => {
    const normalized = normalizeSerial(value);
    if (!normalized) {
      setError("يرجى إدخال الرقم التسلسلي.");
      return;
    }
    setStatus("verifying");
    setError("");
    setPreviewUrl("");
    setVerifiedDocumentId(null);
    try {
      const result = await verifySerial(normalized);
      if (!result.valid) {
        setStatus("error");
        setError("المستند غير صالح.");
        return;
      }
      if (!result.file_exists) {
        setStatus("error");
        setError("الملف غير متوفر في التخزين.");
        return;
      }
      setVerifiedDocumentId(result.document_id);
      setStatus("verified");
      await handleLoadPreview(result.document_id, true);
    } catch (err) {
      setStatus("error");
      setError("تعذر التحقق من المستند.");
    }
  };

  const handleLoadPreview = async (documentId = verifiedDocumentId, open = false) => {
    if (!documentId) {
      return;
    }
    setLoadingPreview(true);
    setError("");
    if (open) {
      setPreviewOpen(true);
    }
    try {
      const blob = await downloadDocument(documentId);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err) {
      setError("???? ????? ????????.");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewUrl("");
  };

  useEffect(() => {
    const initialSerial = searchParams.get("serial");
    if (initialSerial) {
      setSerial(initialSerial);
      handleVerify(initialSerial);
    }
  }, [searchParams]);

  const startCamera = async () => {
    setError("");
    setStatus("scanning");
    setPreviewUrl("");

    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus("error");
      setError("المتصفح لا يدعم الوصول إلى الكاميرا.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      if ("BarcodeDetector" in window) {
        detectorRef.current = new window.BarcodeDetector({ formats: ["qr_code"] });
        useJsQrRef.current = false;
      } else {
        detectorRef.current = null;
        useJsQrRef.current = true;
      }
      scanLoop();
    } catch (err) {
      setStatus("error");
      setError("تعذر تشغيل الكاميرا.");
    }
  };

  const scanLoop = async () => {
    if (!videoRef.current || !canvasRef.current) {
      return;
    }
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");
    if (!context || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(scanLoop);
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    try {
      if (detectorRef.current) {
        const barcodes = await detectorRef.current.detect(canvas);
        if (barcodes.length > 0) {
          const value = barcodes[0].rawValue;
          setSerial(value);
          stopCamera();
          handleVerify(value);
          return;
        }
      } else if (useJsQrRef.current) {
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        const result = jsQR(imageData.data, imageData.width, imageData.height);
        if (result && result.data) {
          const value = result.data;
          setSerial(value);
          stopCamera();
          handleVerify(value);
          return;
        }
      }
    } catch (err) {
      setStatus("error");
      setError("تعذر قراءة رمز QR.");
      stopCamera();
      return;
    }

    rafRef.current = requestAnimationFrame(scanLoop);
  };

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
        <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            التحقق من المستند
          </Typography>
          <Typography color="text.secondary">
            امسح رمز QR أو أدخل الرقم التسلسلي للتحقق من صحة المستند.
          </Typography>
        </CardContent>
      </Card>

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", md: "1.1fr 1fr" } }}>
        <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
          <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="h6">مسح رمز QR</Typography>
            <Box
              sx={{
                position: "relative",
                borderRadius: 2,
                overflow: "hidden",
                border: "1px solid var(--border)",
                backgroundColor: "#0b1220",
                minHeight: 260,
              }}
            >
              <video
                ref={videoRef}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                muted
                playsInline
              />
              <canvas ref={canvasRef} style={{ display: "none" }} />
              <Box
                sx={{
                  position: "absolute",
                  inset: 16,
                  borderRadius: 2,
                  border: "2px dashed rgba(255,255,255,0.5)",
                }}
              />
            </Box>
            <Button variant="outlined" onClick={startCamera} disabled={status === "scanning"}>
              إعادة تشغيل الكاميرا
            </Button>
          </CardContent>
        </Card>

        <Card sx={{ borderRadius: 2, border: "1px solid var(--border)" }}>
          <CardContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Typography variant="h6">إدخال يدوي</Typography>
            <TextField
              label="الرقم التسلسلي"
              value={serial}
              onChange={(event) => setSerial(event.target.value)}
              fullWidth
            />
            <Button variant="contained" onClick={() => handleVerify(serial)} disabled={status === "verifying"}>
              تحقق
            </Button>
            {status === "verified" && !previewUrl ? (
              <Button
                variant="outlined"
                onClick={() => handleLoadPreview(verifiedDocumentId, true)}
                disabled={loadingPreview}
              >
                {loadingPreview ? "جارٍ تحميل المعاينة..." : "عرض الملف"}
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </Box>

      <Dialog
        open={previewOpen}
        onClose={handleClosePreview}
        fullWidth
        maxWidth="lg"
      >
        <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          ?????? ???????
          <IconButton aria-label={"\u0625\u063a\u0644\u0627\u0642"} onClick={handleClosePreview} edge="end">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0, minHeight: 520 }}>
          {loadingPreview ? (
            <Box sx={{ p: 4, textAlign: "center" }}>
              <Typography color="text.secondary">???? ????? ????????...</Typography>
            </Box>
          ) : previewUrl ? (
            <iframe
              title="?????? ???????"
              src={previewUrl}
              style={{ width: "100%", height: "70vh", border: "none" }}
            />
          ) : (
            <Box sx={{ p: 4, textAlign: "center" }}>
              <Typography color="text.secondary">?? ???? ?????? ?????.</Typography>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default VerifyPage;