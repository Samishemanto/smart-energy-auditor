import os
import sys
import shutil
import cv2
import pytesseract


def _find_tesseract() -> str | None:
    # 1. Explicit env var
    env = os.getenv("TESSERACT_CMD")
    if env and os.path.isfile(env):
        return env
    # 2. Common Windows install paths
    for path in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.isfile(path):
            return path
    # 3. On PATH (Linux/Mac/Windows)
    return shutil.which("tesseract")


def _find_poppler() -> str | None:
    # 1. Explicit env var
    env = os.getenv("POPPLER_PATH")
    if env and os.path.isdir(env):
        return env
    # 2. Scan D:\ and C:\ for poppler bin directories (Windows)
    if sys.platform == "win32":
        for drive in ["D:\\", "C:\\"]:
            for root, dirs, _ in os.walk(drive):
                if "poppler" in root.lower() and os.path.isfile(os.path.join(root, "pdftoppm.exe")):
                    return root
                # Avoid scanning too deep
                if root.count(os.sep) - drive.count(os.sep) > 5:
                    dirs.clear()
    # 3. On PATH already
    if shutil.which("pdftoppm"):
        return None  # already on PATH, pdf2image will find it
    return None


_tesseract = _find_tesseract()
if _tesseract:
    pytesseract.pytesseract.tesseract_cmd = _tesseract

_poppler = _find_poppler()


def preprocess_image(file_path: str):
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError(f"Could not read image: {file_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2,
    )


def _pdftotext(file_path: str) -> str:
    """Try to extract text directly from a digital PDF using pdftotext (poppler)."""
    import subprocess
    cmd = ["pdftotext", "-layout", file_path, "-"]
    # On Windows, pdftotext lives inside the poppler bin directory
    if _poppler:
        import os
        exe = os.path.join(_poppler, "pdftotext.exe" if sys.platform == "win32" else "pdftotext")
        if os.path.isfile(exe):
            cmd[0] = exe
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def extract_text(file_path: str) -> str:
    """Extract text from an image or PDF bill. Raises RuntimeError on failure."""
    lower = file_path.lower()

    if lower.endswith(".pdf"):
        # For digital PDFs, try direct text extraction first — far more accurate than OCR
        raw = _pdftotext(file_path)
        if raw.strip():
            lines = [" ".join(line.split()) for line in raw.splitlines()]
            return "\n".join(line for line in lines if line.strip())
        # Fall through to OCR for scanned/image PDFs

    if not _tesseract:
        raise RuntimeError(
            "Tesseract OCR not found. Install it from https://github.com/UB-Mannheim/tesseract/wiki "
            "or set the TESSERACT_CMD environment variable to the tesseract.exe path."
        )

    if lower.endswith((".png", ".jpg", ".jpeg")):
        processed = preprocess_image(file_path)
        text = pytesseract.image_to_string(processed)

    elif lower.endswith(".pdf"):
        from pdf2image import convert_from_path
        kwargs = {"poppler_path": _poppler} if _poppler else {}
        pages = convert_from_path(file_path, **kwargs)
        if not pages:
            raise RuntimeError("PDF produced no pages — file may be corrupt.")
        text = "\n".join(pytesseract.image_to_string(page) for page in pages)

    else:
        raise ValueError("Unsupported file type. Upload PNG, JPG, or PDF.")

    # Preserve line structure: normalise whitespace within each line but keep newlines
    lines = [" ".join(line.split()) for line in text.splitlines()]
    result = "\n".join(line for line in lines if line.strip())
    if not result.strip():
        raise RuntimeError("OCR extracted no text. The bill image may be too dark or low-resolution.")
    return result


if __name__ == "__main__":
    print(extract_text(sys.argv[1] if len(sys.argv) > 1 else "test.png"))
